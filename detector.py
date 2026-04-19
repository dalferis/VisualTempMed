from enum import Enum
from lxml import etree

class FileFormat(Enum):
    XML = 1
    XMI = 2
    E3C = 3
    TML = 4
    OTHER = 999

TYPE_FORMAT_MAP = {
    'xml':     {FileFormat.XML},
    'xmi':     {FileFormat.XMI, FileFormat.E3C},
    'tml-dtd': {FileFormat.TML},
    'tml-xsd': {FileFormat.TML},
}

def detectFormat(xmlfile: str) -> FileFormat:
    is_xmi = False
    try:
        with open(xmlfile, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if '<TimeML' in line:
                    return FileFormat.TML
                if not is_xmi and ('xmi:XMI' in line or 'xmlns:xmi' in line):
                    is_xmi = True
                if is_xmi and ('webanno.custom' in line or 'de.tudarmstadt.ukp.dkpro' in line):
                    return FileFormat.E3C
    except OSError:
        return FileFormat.OTHER

    if is_xmi:
        return FileFormat.XMI

    try:
        etree.parse(xmlfile)
        return FileFormat.XML
    except etree.XMLSyntaxError:
        return FileFormat.OTHER
