import os
import xmlschema
from lxml import etree
from detector import FileFormat

def validateXmiFile(filePath: str, xsdFilePath: str) -> list:
    schema = xmlschema.XMLSchema(xsdFilePath)
    errors = list(schema.iter_errors(filePath))
    if not errors:
        return [True, "XMI well formed"]
    else:
        return [False] + [str(e) for e in errors]

def validateTimeMLFile(filePath: str, xsdFilePath: str) -> list:
    schema = xmlschema.XMLSchema(xsdFilePath)
    errors = list(schema.iter_errors(filePath))
    if not errors:
        return [True, "TimeML well formed"]
    else:
        return [False] + [str(e) for e in errors]

def validateXml(xmlContent: str) -> list:
    try:
        etree.fromstring(xmlContent)
        return [True, "XML well formed"]
    except etree.XMLSyntaxError as e:
        return [False, str(e)]

def validateXmlDtd(xmlContent: str, dtdFilePath: str) -> list:
    try:
        parser = etree.XMLParser(dtd_validation=True)
        dtd = etree.DTD(dtdFilePath)
        xmlDoc = etree.fromstring(xmlContent)
        if dtd.validate(xmlDoc):
            return [True, "XML valid against DTD"]
        else:
            return [False] + [str(e) for e in dtd.error_log]
    except etree.XMLSyntaxError as e:
        return [False, str(e)]

def validateXmlXsd(xmlContent: str, xsdFilePath: str) -> list:
    schema = xmlschema.XMLSchema(xsdFilePath)
    errors = list(schema.iter_errors(xmlContent))
    if not errors:
        return [True, "XML valid against XSD"]
    else:
        return [False] + [str(e) for e in errors]

def validateFile(xmlFile: str, type: str) -> list:
    xmlContent = open(xmlFile, 'r', encoding='utf-8').read()
    if type == 'xml':
        return validateXml(xmlContent)
    elif type == 'xml-dtd':
        return validateXmlDtd(xmlContent, 'XSD/timeml_1.2.1.dtd')
    elif type == 'xml-xsd':
        return validateXmlXsd(xmlContent, 'XSD/TimeML_1.2.2.xsd')
    elif type == 'xmi':
        return validateXmiFile(open(xmlFile, 'r', encoding='utf-8').read(), 'XSD/XMI.xsd')
    elif type == 'tml':
        return validateTimeMLFile(open(xmlFile, 'r', encoding='utf-8').read(), 'XSD/tml.xsd')

def validateDirectory(xmlDirectory, xsdSchema) -> list:
    schema = xmlschema.XMLSchema(xsdSchema)
    result = []
    for file in os.listdir(xmlDirectory):
        print(f"Validating {file}...")
        xmlPath = os.path.join(xmlDirectory, file)
        errors = list(schema.iter_errors(xmlPath))

        if not errors:
            result.append(f"{file}: valid")
        else:
            result.append(f"{file}: {len(errors)} errors")
            for err in errors:
                result.append(f"   - {err}")
    return result
