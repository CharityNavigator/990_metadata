import sys
from lxml import etree
import csv
import glob
import re

# Returns root of etree for which default namespaces have been removed.
# Adapted from Stack Overflow 34009992.
def getRoot(fn):
    with open(fn) as f:
        xmlstring = f.read()

    xmlstring = re.sub(r'\sxmlns="[^"]+"', '', xmlstring, count=1)
    root = etree.fromstring(xmlstring) 
    return root

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

def p2str(path):
    local = path[:]
    local.append("")
    local.reverse()
    return("/".join(local))

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

def getUniqueChildText(elem, cName):
    xp = "xsd:annotation/xsd:documentation/%s" % cName
    ns = {'xsd':'http://www.w3.org/2001/XMLSchema'}
    ds = elem.xpath(xp, namespaces=ns)
    if len(ds) == 0:
        return None
    elif len(ds) == 1:
        return ds[0].text
    else:
        raise AssertionError("Expected %s to be unique" % cName)

def getLineNumber(elem):
    getUniqueChildText(elem, "LineNumber")

def getDescription(elem):
    getUniqueChildText(elem, "Description")

def extract(f, out):
    root = getRoot(f)

    elems = root.xpath("//xsd:element[@name]",
            namespaces={'xsd':'http://www.w3.org/2001/XMLSchema'})
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

    with open("../output/%s_%s.csv" % (year, name), "wb") as outfile:
        out = csv.writer(outfile)
        extract(f, out)

for year in ["2010", "2013"]:
    files = glob.glob("../schema/%s/*.xsd" % year)
    for f in files:
        process(year, f)
