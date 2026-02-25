import xml.etree.ElementTree as ET

def prettyPrintXml(xmlfile: str):
    try:
        tree = ET.parse(xmlfile)
    except:
        print("Error parsing XML file.")

    elementTree = ET.ElementTree(tree.getroot())
    ET.indent(elementTree, space="  ", level=0)
    print(ET.tostring(tree.getroot(), encoding="unicode"))