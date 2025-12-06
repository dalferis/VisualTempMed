from enum import Enum
import xml.etree.ElementTree as ET

class FileFormat(Enum):
    TML = 1
    XMI = 2
    THYME = 3
    E3C_ANNO = 4
    XML = 99
    OTHER = 999

def detectFormat(xmlfile: str) -> FileFormat:
    try:
        tree = ET.parse(xmlfile)
    except:
        return FileFormat.OTHER

    root = tree.getroot()
    if ('timeml' in root.tag.lower()):
        return FileFormat.TML

    if ('xmi' in root.tag.lower()):
        return FileFormat.XMI

    return FileFormat.XML

def detectFormatInFile(filepath: str) -> FileFormat:
    return detectFormat(filepath)

def detectFormatInDirectory(directory: str) -> dict:
    import os
    formats = {}
    for file in os.listdir(directory):
        formats[file] = detectFormat(os.path.join(directory, file))
    return formats