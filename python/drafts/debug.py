from lxml import etree
import re

def getRoot(fn):
    with open(fn) as f:
        xmlstring = f.read()

    xmlstring = re.sub(r'\sxmlns="[^"]+"', '', xmlstring, count=1)
    root = etree.fromstring(xmlstring) 
    return root

root = getRoot("../../schema/2010/IRS990.xsd")

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


elems = root.xpath("//xsd:element[@name]", namespaces={'xsd':'http://www.w3.org/2001/XMLSchema'})
for elem in elems:
    print getUniqueChildText(elem, "Description")
