from lxml import etree

def traverse(root, parents = [""]):
    local = parents[:]

    # Document root lacks a name; everything else should have one
    if root.tag != "{http://www.w3.org/2001/XMLSchema}schema":
        rootName = root.attrib["name"]
        local.append(rootName)

    # element 
    elems = root.xpath("xsd:element[@name]",
            namespaces={'xsd':'http://www.w3.org/2001/XMLSchema'})

    if len(elems) == 0:
        print "/".join(local)

    for elem in elems:
        traverse(elem, local)

    # complexType
    # group

tree = etree.parse("IRS990.xsd")
root = tree.getroot()

#traverse(root)

elems = root.xpath("//xsd:element[@name]", namespaces={'xsd':'http://www.w3.org/2001/XMLSchema'})
for elem in elems:
    print
    print elem.attrib["name"] 
    print elem.tag
    print elem.xpath
