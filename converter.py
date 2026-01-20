#from asyncio import events
#from os import eventfd
from asyncio import events
import re
from cassis import *
from lxml import etree
import json
import logging
import validator

logging.basicConfig(level=logging.DEBUG)

translations = {
    "OCCURRENCE": "OCCURRENCE",
    "ASPECTUAL": "ASPECTUAL",
    "PERCEPTION": "PERCEPTION",
    "I_ACTION": "I_ACTION",
    "I_STATE": "I_STATE",
    "STATE": "STATE",
    "REPORTING": "REPORTING",
    "EVIDENTIAL": "EVIDENTIAL",
    "INTENTION": "INTENTION",
    "NEGATION": "NEGATION"
}

def TIMEX3(cas, text):
    timexes = []
    timex_id_map = {}

    for i, t in enumerate(cas.select("webanno.custom.TIMEX3"), start=1):
        tid = make_id("t", i)
        timex_id_map[t.xmiID] = tid

        timexes.append({
            "tid": tid,
            "begin": t.begin,
            "end": t.end,
            "text": text[t.begin:t.end],
            "type": t.timex3Class,
            "value": t.value
        })
    return timexes, timex_id_map

def TLINK(cas, event_id_map, timex_id_map):
    tlinks = []

    for l in cas.select("webanno.custom.EVENTTLINKLink"):
        source = event_id_map.get(l.xmiID)
        target = timex_id_map.get(l.target)

        if source and target:
            tlinks.append({
                "eventInstanceID": source,
                "relatedToTime": target,
                "relType": l.role
            })
    return tlinks

def get_docid(cas):
    dmd_list = cas.select("de.tudarmstadt.ukp.dkpro.core.api.metadata.type.DocumentMetaData")
    if not dmd_list:
        return "UNKNOWN_DOCID"
    return dmd_list[0].documentId

def event(root, cas):
    text = cas.sofa_string
    events = list(cas.select("webanno.custom.EVENT")) + [{"begin": len(text)}]
    text_el = etree.SubElement(root, "TEXT")
    text_el.text = text[0:events[0]["begin"]]

    for i, e in enumerate(events[:-2], start=1):
        event_el = etree.SubElement(
            text_el,
            "EVENT",
            attrib = {
                "eid":f"e{i}",
                "class": "OCCURRENCE" if e["eventType"] == "N/A" else e["eventType"],
            }
        )
        event_el.text = text[e["begin"]:e["end"]]
        event_el.tail = text[e["end"]:events[i+1]["begin"]]

    return text_el

def generateTimeML(cas):
    etree.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root = etree.Element("TimeML")
    root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", "TimeML_1.2.1.xsd")

    etree.SubElement(root, "DOCID").text = get_docid(cas)

    text_el = event(root, cas)

    return root


def convertFile(xmlfile: str, typesystemfile: str):
    with open(typesystemfile, 'rb') as f:
        typesystem = load_typesystem(f)

    with open(xmlfile, 'rb') as f:
        cas = load_cas_from_xmi(f, typesystem=typesystem)

    # print("Document text:", cas.sofa_string)
    # with open(xmlfile + ".json", 'w', encoding='utf-8') as out_f:
    #     out_f.write(json.dumps(json.loads(cas.to_json()), indent=2))

    # events, event_id_map = EVENT(cas, cas.sofa_string)
    # timexes, timex_id_map = TIMEX3(cas, cas.sofa_string)
    # tlinks = TLINK(cas, event_id_map, timex_id_map)
    tml = generateTimeML(cas)

    print(etree.tostring(tml, pretty_print=True, encoding="unicode"))


    with open(xmlfile + ".tml", 'w', encoding='utf-8') as out_f:
        out_f.write(etree.tostring(tml, pretty_print=True, xml_declaration=True, encoding="UTF-8").decode("utf-8"))
    result = validator.validateFile(xmlfile + ".tml", "xml-xsd")
    print("\n".join(result[1:]))
    with open("validation_report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(result[1:]))


    # print(json.dumps(json.loads(cas.to_json()), indent=2))
