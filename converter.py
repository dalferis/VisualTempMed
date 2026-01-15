from asyncio import events
#from os import eventfd
import re
from cassis import *
from lxml import etree
import json
import logging

logging.basicConfig(level=logging.DEBUG)

def make_id(prefix, n):
    return f"{prefix}{n}"

def EVENT(cas, text):
    events = []
    event_id_map = {}

    for i, e in enumerate(cas.select("webanno.custom.EVENT"), start=1):
        eid = make_id("e", i)
        event_id_map[e.xmiID] = eid

        events.append({
            "eid": eid,
            "begin": e.begin,
            "end": e.end,
            "text": text[e.begin:e.end],
            "class": e.eventType if hasattr(e, "eventType") else "OCCURRENCE",
            "polarity": e.polarity,
            "tense": "NONE",
            "aspect": "NONE"
        })
    return events, event_id_map

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


def generateTimeML(cas, text, events, timexes, tlinks):
    root = etree.Element("TimeML")

    etree.SubElement(root, "DOCID").text = get_docid(cas)

    text_el = etree.SubElement(root, "TEXT")
    text_el.text = text

    for e in events:
        ev = etree.SubElement(text_el, "EVENT", eid=e["eid"], class_=e.get("class", "OCCURRENCE"), polarity=e.get("polarity", "POS"))
        ev.text = e["text"]

    for t in timexes:
        tx = etree.SubElement(text_el, "TIMEX3", tid=t["tid"], type=t["type"], value=t["value"])
        tx.text = t["text"]

    for i, l in enumerate(tlinks, start=1):
        etree.SubElement(root, "TLINK", lid=f"l{i}", eventInstanceID=l.get("eventInstanceID"), relatedToTime=l.get("relatedToTime"), relType=l["relType"])

    return root


def convertFile(xmlfile: str, typesystemfile: str):
    with open(typesystemfile, 'rb') as f:
        typesystem = load_typesystem(f)

    with open(xmlfile, 'rb') as f:
        cas = load_cas_from_xmi(f, typesystem=typesystem)

    print("Document text:", cas.sofa_string)

    # with open(xmlfile + ".json", 'w', encoding='utf-8') as out_f:
    #     out_f.write(json.dumps(json.loads(cas.to_json()), indent=2))

    events, event_id_map = EVENT(cas, cas.sofa_string)
    timexes, timex_id_map = TIMEX3(cas, cas.sofa_string)
    tlinks = TLINK(cas, event_id_map, timex_id_map)
    tml = generateTimeML(cas, cas.sofa_string, events, timexes, tlinks)

    print(etree.tostring(tml, pretty_print=True, encoding="unicode"))


    # with open(xmlfile + ".tml", 'w', encoding='utf-8') as out_f:
    #     out_f.write(etree.tostring(tml, pretty_print=True, xml_declaration=True, encoding="UTF-8"))

    # print(json.dumps(json.loads(cas.to_json()), indent=2))
