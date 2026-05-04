from enum import Enum
from lxml import etree

class FileFormat(Enum):
    XML = 1
    XMI = 2
    E3C = 3
    TML = 4
    OTHER = 999

def detectFormatContent(xmlContent: str) -> FileFormat:
    is_xmi = False
    for line in xmlContent.splitlines():
        if '<TimeML' in line:
            return FileFormat.TML
        if not is_xmi and ('xmi:XMI' in line or 'xmlns:xmi' in line):
            is_xmi = True
        if is_xmi and ('webanno.custom' in line or 'de.tudarmstadt.ukp.dkpro' in line):
            return FileFormat.E3C

    if is_xmi:
        return FileFormat.XMI

    try:
        etree.fromstring(xmlContent.encode('utf-8'))
        return FileFormat.XML
    except etree.XMLSyntaxError:
        return FileFormat.OTHER


def detectFormatFile(xmlFile: str) -> FileFormat:
    try:
        with open(xmlFile, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except OSError:
        return FileFormat.OTHER
    return detectFormatContent(content)
