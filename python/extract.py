from lxml import etree
import re
import csv
import sys
import glob
import os.path

NAMESPACE = {'xsd':'http://www.w3.org/2001/XMLSchema'} 

class UnhandledElementException(Exception):
    pass

class Node:
    def __init__(self, elem, version, xpref):
        # Raw fields
        self.elem      = elem
        self.version   = version 
        self.xpref     = xpref
        self.apath     = self.ascend(elem)
        self.namespace = self.getNamespace(self.apath[-1])
        self.process()

    def compose(self, prefix, namespace):
        composite = Node(self.elem, self.version, self.xpref)
        composite.xpath = "/".join([prefix, self.xpath])
        composite.namespace = namespace
        return composite

    def ascend(self, node, path = []):
        local = path[:]
        abbr = abbreviate(node)

        if not abbr in ["schema"]:
            local.append(abbr)

        parent = node.getparent()

        if parent == None:
            return local

        return self.ascend(parent, local)

    # Xpath to this node (relative to namespace)
    def getXpath(self):
        p = []

        for token in reversed(self.apath):
            if (not self.namespace == None) and (":" in token) and\
                    (token.endswith(self.namespace)):
                continue
            if token in ["sequence", "choice", "complexType"]:
                continue

            token = token.split(":")[-1]
            p.append(token)
        xp = "/".join(p)
        return "/".join(p)

    def getNamespace(self, token):
        if token.startswith("group:"):
            return token.split(":")[-1]

        if token.startswith("complexType:"):
            return token.split(":")[-1]

        return None

    def getAttrib(self, attr):
        if attr in self.elem.attrib:
            return self.elem.attrib[attr]

        return None

    # Type attribute from XML
    def getType(self):
        # In-line type specifications
        if "type" in self.elem.attrib:
            return self.elem.attrib["type"]
       
        # Nested type specifications -- complexType
        cplxElems = getByXpath(self.elem,
                "xsd:complexType/*/xsd:extension[@base]")

        if len(cplxElems) == 1:
            return cplxElems[0].attrib["base"]

        # Nested type specification -- simpleType
        smplElems = getByXpath(self.elem,
                "xsd:simpleType/xsd:restriction[@base]")

        if len(smplElems) == 1:
            return smplElems[0].attrib["base"]

        raise UnhandledElementException("/".join(self.ascend(self.elem)))

    def getUniqueChildText(self, cName):
        xp = "xsd:annotation/xsd:documentation/%s" % cName
        ds = getByXpath(self.elem, xp)
        if len(ds) == 0:
            return None
        elif len(ds) == 1:
            return ds[0].text
        else:
            raise AssertionError("Expected %s to be unique" % cName)

    def getMin(self):
        return self.getAttrib("minOccurs")

    def getMax(self):
        return self.getAttrib("maxOccurs")

    def getLineNumber(self):
        return self.getUniqueChildText("LineNumber")

    def getDescription(self):
        return self.getUniqueChildText("Description")

    def process(self):
        self.eType = self.getType()
        self.xpath = self.getXpath()
        self.desc = self.getDescription()
        self.lineNum = self.getLineNumber()
        self.minOccur = self.getMin()
        self.maxOccur = self.getMax()


    def examine(self):
        return [self.namespace, 
                self.apath]

    # Return the version of the node's data to be published in the data
    # dictionary.
    def report(self):

        # By the time this code is called, the Xpath should reflect the prefix
        # that was stripped for processing earlier.
        pubXpath = "/".join([self.xpref, self.xpath])

        ret = [self.version, pubXpath, self.eType, self.desc, self.lineNum,
                self.minOccur, self.maxOccur]

        return [strip(x) for x in ret]

def strip(s):
    if s == None:
        return None

    return s.encode("ascii", "ignore")
# Returns root of etree for which default namespaces have been removed.
# Adapted from Stack Overflow 34009992.
def getRoot(fn):
    with open(fn) as f:
        xmlstring = f.read()

    xmlstring = re.sub(r'\sxmlns="[^"]+"', '', xmlstring, count=1)
    root = etree.fromstring(xmlstring) 
    return root

def getByXpath(elem, xp):
    return elem.xpath(xp, namespaces=NAMESPACE)


def nsAdd(tbl, key, content):
    if not key in tbl:
        tbl[key] = set()

    assert content != None

    tbl[key].add(content)

def concat(prefix, child):
    path = ascend(child)
    suffix = "/".join(path[1:])
    units = [prefix, suffix]
    return "/".join(units)

def resolve(elem):
    eType = getType(elem)

    if eType in namespaces:
        remap(elem, namespaces[eType])
    else:
        report(elem)

def abbreviate(node):
    ns = re.escape("{http://www.w3.org/2001/XMLSchema}")
    tag = re.sub(ns, "", node.tag)

    ret = [tag]

    if "name" in node.attrib:
        ret.append(node.attrib["name"])

    return ":".join(ret)

def remap(nodes, namespaces):
    local = nodes.copy()

    while True:
        current = local.copy()

        for node in current:
            t = node.eType
            ns = node.namespace
            if t != None and t in namespaces.keys():
                prefix = node.xpath

                local.remove(node)
                namespaces[ns].remove(node)

                for child in namespaces[t]:
                    composite = child.compose(prefix, ns)
                    assert composite != None
                    namespaces[ns].add(composite)
                    local.add(composite)

        # Break if local is unchanged
        if len(local.difference(current)) == 0:
            break

        current = local

    return local 


def process(xpref, fn):
    # Set of all element nodes.
    nodes = set()

    # Elements that exist as part of a type definition. This information will
    # be used in constructing composite xpaths and side tables.
    namespaces = {}

    version = fn.split("/")[2]
    root = getRoot(fn)
    xp = "//xsd:element[@name]"
    elems = getByXpath(root, xp)

    for elem in elems:
        try:
            node = Node(elem, version, xpref)
        except UnhandledElementException, e:
            print "!SKIPPED: %s" % str(e)
            continue

        ns = node.namespace 

        assert node != None

        nsAdd(namespaces, ns, node)
        nodes.add(node)

    nodes = remap(nodes, namespaces)

    lines = [n.report() for n in namespaces[None]]
    return lines

lines = []
files = {"TEGE/TEGE990/IRS990/IRS990.xsd" : "Return/ReturnData",
         "TEGE/TEGE990EZ/IRS990EZ/IRS990EZ.xsd" : "Return/ReturnData",
         "TEGE/Common/ReturnHeader990x.xsd" : "Return",
         "TEGE/Common/IRS990ScheduleA/IRS990ScheduleA.xsd" : "Return/ReturnData",
         "TEGE/Common/IRS990ScheduleB/IRS990ScheduleB.xsd" : "Return/ReturnData",
         "TEGE/Common/IRS990ScheduleC/IRS990ScheduleC.xsd" : "Return/ReturnData",
         "TEGE/Common/IRS990ScheduleD/IRS990ScheduleD.xsd" : "Return/ReturnData",
         "TEGE/Common/IRS990ScheduleE/IRS990ScheduleE.xsd" : "Return/ReturnData",
         "TEGE/Common/IRS990ScheduleF/IRS990ScheduleF.xsd" : "Return/ReturnData",
         "TEGE/Common/IRS990ScheduleG/IRS990ScheduleG.xsd" : "Return/ReturnData",
         "TEGE/Common/IRS990ScheduleH/IRS990ScheduleH.xsd" : "Return/ReturnData",
         "TEGE/Common/IRS990ScheduleI/IRS990ScheduleI.xsd" : "Return/ReturnData",
         "TEGE/Common/IRS990ScheduleJ/IRS990ScheduleJ.xsd" : "Return/ReturnData",
         "TEGE/Common/IRS990ScheduleK/IRS990ScheduleK.xsd" : "Return/ReturnData",
         "TEGE/Common/IRS990ScheduleL/IRS990ScheduleL.xsd" : "Return/ReturnData",
         "TEGE/Common/IRS990ScheduleM/IRS990ScheduleM.xsd" : "Return/ReturnData",
         "TEGE/Common/IRS990ScheduleN/IRS990ScheduleN.xsd" : "Return/ReturnData",
         "TEGE/Common/IRS990ScheduleO/IRS990ScheduleO.xsd" : "Return/ReturnData",
         "TEGE/Common/IRS990ScheduleP/IRS990ScheduleP.xsd" : "Return/ReturnData",
         "TEGE/Common/IRS990ScheduleQ/IRS990ScheduleQ.xsd" : "Return/ReturnData",
         "TEGE/Common/IRS990ScheduleR/IRS990ScheduleR.xsd" : "Return/ReturnData"}

versions = glob.glob("../schema/*")
for version in versions:
    for fn in files:
        path = "%s/%s" % (version, fn)
        if os.path.exists(path):
            xpref = files[fn]
            local = process(xpref, path)
            lines.extend(local)

with open("../output/xpath_all.csv", "wb") as outfile:
    out = csv.writer(outfile)
    out.writerow(["Version","Xpath","Type","Description","Line","MinOccur","MaxOccur"])
    out.writerows(lines)

print "\nDone"
