import os
import xmlschema
from lxml import etree
from detector import FileFormat, detectFormat, TYPE_FORMAT_MAP

def validateXml(xmlContent: str) -> list:
    try:
        etree.fromstring(xmlContent.encode('utf-8'))
        return [True, "XML well-formed"]
    except etree.XMLSyntaxError as e:
        return [False, str(e)]

def validateXmi(filePath: str, xsdFilePath: str) -> list:
    schema = xmlschema.XMLSchema(xsdFilePath)
    errors = list(schema.iter_errors(filePath))
    if not errors:
        return [True, "XMI valid against XSD"]
    else:
        return [False] + [str(e) for e in errors]

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
    elif type == 'xmi':
        return validateXmi(xmlContent, 'XSD/XMI.xsd')
    elif type == 'tml':
        return validateXmlXsd(xmlContent, 'XSD/TimeML_1.2.xsd')

def validate(xmlPath: str, type: str, report_file: str = "validation_report.txt"):
    NUMBER_OF_LINES_TO_PRINT = 10

    def _reportResult(f, name, result):
        valid = result[0]
        lines = result[1:]
        message = f"{name}: {'valid' if valid else f'{len(lines)} errors'}\n"
        print(message)
        f.write(message)
        if not valid:
            print("\n".join([f"   - {chr(10).join(str(e).splitlines()[:NUMBER_OF_LINES_TO_PRINT])}" for e in lines]) + "\n")
            f.write("\n".join([f"   - {e}" for e in lines]) + "\n")

    if os.path.isfile(xmlPath):
        with open(report_file, "w", encoding="utf-8") as f:
            _reportResult(f, os.path.basename(xmlPath), validateFile(xmlPath, type))
    elif os.path.isdir(xmlPath):
        with open(report_file, "w", encoding="utf-8") as f:
            for file in os.listdir(xmlPath):
                filePath = os.path.join(xmlPath, file)
                if not os.path.isfile(filePath):
                    continue
                detected = detectFormat(filePath)
                if detected not in TYPE_FORMAT_MAP.get(type, set()):
                    print(f"Skipping {file} (format: {detected.name})")
                    continue
                print(f"Validating {file}...")
                _reportResult(f, file, validateFile(filePath, type))
    else:
        print(f"Error: '{xmlPath}' is not a valid file or directory")
