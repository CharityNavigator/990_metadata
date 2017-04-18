import sys
from lxml import etree
import csv
import glob
import re

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

def extract(f, out):
    tree = etree.parse(f)
    root = tree.getroot()

    elems = root.xpath("//xsd:element[@name]", namespaces={'xsd':'http://www.w3.org/2001/XMLSchema'})
    for elem in elems:
        path = ascend(elem)
        out.writerow([p2str(path)])

def process(year, f):
    name = f.split("/")[-1].split(".")[0]

    with open("../output/%s_%s.csv" % (year, name), "wb") as outfile:
        out = csv.writer(outfile)
        extract(f, out)

for year in ["2010", "2013"]:
    files = glob.glob("../schema/%s/*.xsd" % year)
    for f in files:
        process(year, f)
