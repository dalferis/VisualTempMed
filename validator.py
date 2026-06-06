import xmlschema
from lxml import etree


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
    xsd_result = validateXmlXsd(xmlContent, 'XSD/TimeML_1.2.4.xsd')
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
