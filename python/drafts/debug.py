from lxml import etree
import re
import csv

NAMESPACE = {'xsd':'http://www.w3.org/2001/XMLSchema'} 

def getRoot(fn):
    with open(fn) as f:
        xmlstring = f.read()

    xmlstring = re.sub(r'\sxmlns="[^"]+"', '', xmlstring, count=1)
    root = etree.fromstring(xmlstring) 
    return root

def getByXpath(elem, xp):
    return elem.xpath(xp, namespaces=NAMESPACE)

def getUniqueChildText(elem, cName):
    xp = "xsd:annotation/xsd:documentation/%s" % cName
    ds = getByXpath(elem, xp)
    if len(ds) == 0:
        return None
    elif len(ds) == 1:
        return ds[0].text
    else:
        raise AssertionError("Expected %s to be unique" % cName)

def p2str(path):
    local = path[:]
    local.append("")
    local.reverse()
    return("/".join(local))

def abbreviate(node):
    ns = re.escape("{http://www.w3.org/2001/XMLSchema}")
    tag = re.sub(ns, "", node.tag)

    ret = [tag]

    if "name" in node.attrib:
        ret.append(node.attrib["name"])

    return ":".join(ret)

def ascend(node, path = []):
    local = path[:]
    abbr = abbreviate(node)
    local.append(abbr)

    parent = node.getparent()

    if parent == None:
        return local

    return ascend(parent, local)

def getAttrib(elem, attr):
    if attr in elem.attrib:
        return elem.attrib[attr]

    return None

def getType(elem):
    return getAttrib(elem, "type")

def getMin(elem):
    return getAttrib(elem, "minOccurs")

def getMax(elem):
    return getAttrib(elem, "maxOccurs")

def getLineNumber(elem):
    return getUniqueChildText(elem, "LineNumber")

def getDescription(elem):
    return getUniqueChildText(elem, "Description")

def extract(f, out):
    root = getRoot(f)
    xp = "//xsd:element[@name]"
    elems = getByXpath(root, xp)

    for elem in elems:
        path = ascend(elem)
        eType = getType(elem)
        eMin  = getMin(elem)
        eMax  = getMax(elem)
        eLine = getLineNumber(elem)
        eDesc = getDescription(elem)
        print eDesc
        out.writerow([p2str(path), eType, eLine, eDesc, eMin, eMax])

def process(year, f):
    name = f.split("/")[-1].split(".")[0]

    with open("../../output/%s_%s.csv" % (year, name), "wb") as outfile:
        out = csv.writer(outfile)
        extract(f, out)

process(2010, "../../schema/2010/IRS990.xsd")
