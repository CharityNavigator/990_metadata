from lxml import etree
import re

tree = etree.parse("IRS990.xsd")
root = tree.getroot()

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

elems = root.xpath("//xsd:element[@name]", namespaces={'xsd':'http://www.w3.org/2001/XMLSchema'})
for elem in elems:
    path = ascend(elem)
    print p2str(path)
