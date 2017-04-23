from lxml import etree
import re
import csv
import sys
import glob

class BizarreElementException(Exception):
    pass

NAMESPACE = {'xsd':'http://www.w3.org/2001/XMLSchema'} 

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

    if not abbr in ["sequence", "schema", "choice"]:
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
    # In-line type specifications
    if "type" in elem.attrib:
        return elem.attrib["type"]
   
    # Nested type specifications
    extElems = getByXpath(elem, "xsd:complexType/*/xsd:extension[@base]")

    if len(extElems) == 1:
        return extElems[0].attrib["base"]

    raise BizarreElementException(p2str(ascend(elem)))

def getByXpath(elem, xp):
    return elem.xpath(xp, namespaces=NAMESPACE)

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
        try:
            path = ascend(elem)
            eType = getType(elem)
            eMin  = getMin(elem)
            eMax  = getMax(elem)
            eLine = getLineNumber(elem)
            eDesc = getDescription(elem)
            out.writerow([p2str(path), eType, eLine, eDesc, eMin, eMax])
        except BizarreElementException, e:
            print str(e)
            continue

def process(year, f):
    name = f.split("/")[-1].split(".")[0]

    with open("../output/%s_%s.csv" % (year, name), "w") as outfile:
        out = csv.writer(outfile)
        extract(f, out)

for year in ["2010", "2013"]:
    files = glob.glob("../schema/%s/*.xsd" % year)
    for f in files:
        process(year, f)
