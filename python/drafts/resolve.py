from lxml import etree
import re
import csv
import sys
import glob

NAMESPACE = {'xsd':'http://www.w3.org/2001/XMLSchema'} 

class UnhandledElementException(Exception):
    pass

class Node:
    def compose(self, prefix, namespace):
        composite = Node(self.elem)
        composite.xpath = "".join([prefix, self.xpath])
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

        p.insert(0, "")
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
       
        # Nested type specifications
        extElems = getByXpath(self.elem,
                "xsd:complexType/*/xsd:extension[@base]")

        if len(extElems) == 1:
            return extElems[0].attrib["base"]

        raise UnhandledElementException("/".join(self.ascend(elem)))

    def process(self):
        self.eType = self.getType()
        self.xpath = self.getXpath()

    def __init__(self, elem):
        # Raw fields
        self.elem      = elem
        self.apath     = self.ascend(elem)
        self.namespace = self.getNamespace(self.apath[-1])
        self.process()

        # Processed fields
        self.table     = None  # Name of table in which node occurs
        self.desc      = None  # IRS description
        self.minOccur  = None  # Minimum number of occurrences
        self.maxOccur  = None  # Maximum number of occurrences
        self.lineNum   = None  # Line number

    def examine(self):
        return [self.namespace, 
                self.apath]

    def report(self):
        return [self.xpath,
                self.eType,
                self.table,
                self.xpath,
                self.desc,
                self.lineNum,
                self.minOccur,
                self.maxOccur]


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

# Set of all element nodes.
nodes = set()

# Elements that exist as part of a type definition. This information will be
# used in constructing composite xpaths and side tables.
namespaces = {}

root = getRoot("../../schema/2010/IRS990.xsd")
xp = "//xsd:element[@name]"
elems = getByXpath(root, xp)

for elem in elems:
    try:
        node = Node(elem)
    except UnhandledElementException, e:
        print "!ERROR: %s" % str(e)
        continue

    ns = node.namespace 

    assert node != None

    nsAdd(namespaces, ns, node)
    nodes.add(node)

nodes = remap(nodes, namespaces)

print
for k in namespaces.keys():
    print "***%s***" % k
    v = namespaces[k]
    for n in v:
        print [n.namespace, n.eType, n.xpath]

    print "\n\n"

print "Done"
