import os
import xmlschema
from lxml import etree
from detector import FileFormat, detectFormatFile


def validateXmlXsd(xmlContent: str, xsdFilePath: str) -> list:
    schema = xmlschema.XMLSchema(xsdFilePath)
    errors = list(schema.iter_errors(xmlContent))
    if not errors:
        return [True, "XML valid against XSD"]
    else:
        return [False] + [str(e) for e in errors]


def tmlSpecValidation(xmlContent: str) -> list:
    """
    Spec-only checks, not enforced by the XSD.
    """
    try:
        root = etree.fromstring(xmlContent.encode('utf-8'))
    except etree.XMLSyntaxError as e:
        return [False, str(e)]

    errors = []

    referenced_event_ids = {mi.get('eventID') for mi in root.iter('MAKEINSTANCE')}
    for event in root.iter('EVENT'):
        eid = event.get('eid')
        if eid not in referenced_event_ids:
            errors.append(f"EVENT '{eid}' has no corresponding MAKEINSTANCE")

    if not errors:
        return [True, "TimeML spec checks passed"]
    return [False] + errors


def validateContent(xmlContent: str) -> list:
    xsd_result = validateXmlXsd(xmlContent, 'XSD/TimeML_1.2.3.xsd')
    spec_result = tmlSpecValidation(xmlContent)
    if xsd_result[0] and spec_result[0]:
        return [True, "Valid against XSD and TimeML spec"]
    errors = []
    if not xsd_result[0]:
        errors += xsd_result[1:]
    if not spec_result[0]:
        errors += spec_result[1:]
    return [False] + errors


def validateFile(xmlFile: str) -> list:
    with open(xmlFile, 'r', encoding='utf-8') as f:
        xmlContent = f.read()
    return validateContent(xmlContent)


def validate(xmlPath: str, report_file: str = "validation_report.txt"):
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
            _reportResult(f, os.path.basename(xmlPath), validateFile(xmlPath))
    elif os.path.isdir(xmlPath):
        with open(report_file, "w", encoding="utf-8") as f:
            for file in os.listdir(xmlPath):
                filePath = os.path.join(xmlPath, file)
                if not os.path.isfile(filePath):
                    continue
                detected = detectFormatFile(filePath)
                if detected != FileFormat.TML:
                    print(f"Skipping {file} (format: {detected.name})")
                    continue
                print(f"Validating {file}...")
                _reportResult(f, file, validateFile(filePath))
    else:
        print(f"Error: '{xmlPath}' is not a valid file or directory")
