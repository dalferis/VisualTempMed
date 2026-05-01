import xml.etree.ElementTree as ET
import xmlschema
from lxml import etree


def prettyPrintXml(xmlfile: str):
    try:
        tree = ET.parse(xmlfile)
    except:
        print("Error parsing XML file.")

    elementTree = ET.ElementTree(tree.getroot())
    ET.indent(elementTree, space="  ", level=0)
    print(ET.tostring(tree.getroot(), encoding="unicode"))


def validateXml(xmlContent: str) -> list:
    try:
        etree.fromstring(xmlContent.encode('utf-8'))
        return [True, "XML well-formed"]
    except etree.XMLSyntaxError as e:
        return [False, str(e)]


def validateXmi(xmlContent: str, xsdFilePath: str) -> list:
    schema = xmlschema.XMLSchema(xsdFilePath)
    errors = list(schema.iter_errors(xmlContent))
    if not errors:
        return [True, "XMI valid against XSD"]
    else:
        return [False] + [str(e) for e in errors]
