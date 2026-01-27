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

# Syntax:
# translate[<e3c_tag>][<e3c_attrib>][<e3c_value>] = { "tag":<tml_tag>, "attrib":<tml_attrib>, "value":<tml_value> }
# Example:
# translate["EVENT"]["eventType"]["OCCURRENCE"] returns { "tag": "EVENT", "attrib": "class", "value": "OCCURRENCE" }
# translate["EVENT"] = {
#     "eventType": {
#         "tag": "EVENT",
#         "attrib": "class",
#         "value": {
#             "N/A": "OCCURRENCE",
#             "ASPECTUAL": "ASPECTUAL",
#             "EVIDENTIAL": "PERCEPTION"
#         }
#     }
# }

# Syntax:
# translate[<e3c_tag>][<e3c_attrib>][<e3c_value>] = <tml_value>
# Example:
# translate["EVENT"]["eventType"]["N/A"] returns "OCCURRENCE"
translate = {}
translate["EVENT"] = {
    "eventType": {
        "N/A": "OCCURRENCE",
        "ASPECTUAL": "ASPECTUAL",
        "EVIDENTIAL": "PERCEPTION"
    },
    "docTimeRel": {
        "BEFORE": "PAST",
        "AFTER": "FUTURE",
        "CONTAINS": "PRESENT",
        "OVERLAP": "PRESENT",
        "INCLUDES": "PRESENT",
        "IS-INCLUDED": "PRESENT",
        "IS-CONTAINED": "PRESENT",
        "SIMULTANEOUS": "PRESENT"
    }
}
translate["TLINK"] = {
    "role": {
        "BEFORE": "BEFORE",
        "CONTAINS": "INCLUDES",
        "SIMULTANEOUS": "SIMULTANEOUS",
        "OVERLAP": "DURING",
        "BEGINS-ON": "BEGINS",
        "ENDS-ON": "ENDS"
    }
}

def get_docid(cas):
    dmd_list = cas.select("de.tudarmstadt.ukp.dkpro.core.api.metadata.type.DocumentMetaData")
    if not dmd_list:
        return "UNKNOWN_DOCID"
    return dmd_list[0].documentId

def event(root, cas):
    event_id_map = {}
    timex3_id_map = {}
    tml_tlinks = []
    text = cas.sofa_string
    cas_events = list(cas.select("webanno.custom.EVENT")) + list(cas.select("webanno.custom.TIMEX3")) + [{"begin": len(text)}]
    cas_events = sorted(cas_events, key=lambda e: e["begin"])
    text_el = etree.SubElement(root, "TEXT")
    text_el.text = text[0:cas_events[0]["begin"]]

    tlink_count = 0
    event_count = 1
    timex3_count = 1
    for e in cas_events[:-1]:
        if e.type.name == "webanno.custom.EVENT":
            event_el = etree.SubElement(text_el, "EVENT",
                attrib = {
                    "eid":f"e{event_count}",
                    "class": translate["EVENT"]["eventType"][e["eventType"]],
                }
            )
            event_el.text = text[e["begin"]:e["end"]]
            event_el.tail = text[e["end"]:cas_events[event_count]["begin"]]
            etree.SubElement(root, "MAKEINSTANCE",
                attrib = {
                    "eventID":f"e{event_count}",
                    "eiid":f"ei{event_count}",
                    "pos":"OTHER",
                    "tense":translate["EVENT"]["docTimeRel"][e["docTimeRel"]],
                    "aspect":"NONE",
                    "polarity":e["polarity"]
                    #"cardinality":"",
                    #"modality":""
                }
            )
            event_id_map[e.xmiID] = f"ei{event_count}"
            for j, tl in enumerate(e.TLINK.elements, start=1):
                tml_tlinks.append({
                    "lid":f"l{tlink_count+j}",
                    "eventInstanceID":f"ei{event_count+1}",
                    "relType":translate["TLINK"]["role"][tl.role],
                })
                if tl.target.type.name == "webanno.custom.TIMEX3":
                    tml_tlinks[-1]["relatedToTime"] = tl.target.xmiID
                elif tl.target.type.name == "webanno.custom.EVENT":
                    tml_tlinks[-1]["relatedToEventInstance"] = tl.target.xmiID
            tlink_count += len(e.TLINK.elements)
            event_count += 1
        elif e.type.name == "webanno.custom.TIMEX3":
            timex3_el = etree.SubElement(text_el, "TIMEX3",
                attrib = {
                    "tid":f"t{timex3_count}",
                    "type": e.timex3Class,
                    "value": e.value
                }
            )
            timex3_el.text = text[e["begin"]:e["end"]]
            timex3_el.tail = text[e["end"]:cas_events[event_count+timex3_count]["begin"]]
            timex3_id_map[e.xmiID] = f"t{timex3_count}"
            timex3_count += 1
    for tl in tml_tlinks:
        if ("relatedToTime" in tl):
            if tl["relatedToTime"] in event_id_map:
                tl["relatedToTime"] = event_id_map[tl["relatedToTime"]]
                etree.SubElement(root, "TLINK", attrib=tl)
        elif ("relatedToEventInstance" in tl):
            if tl["relatedToEventInstance"] in event_id_map:
                tl["relatedToEventInstance"] = event_id_map[tl["relatedToEventInstance"]]
                etree.SubElement(root, "TLINK", attrib=tl)

def generateTimeML(cas):
    etree.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root = etree.Element("TimeML")
    root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", "TimeML_1.2.1.xsd")

    etree.SubElement(root, "DOCID").text = get_docid(cas)

    event(root, cas)

    return root


def convertFile(xmlfile: str, typesystemfile: str):
    with open(typesystemfile, 'rb') as f:
        typesystem = load_typesystem(f)

    with open(xmlfile, 'rb') as f:
        cas = load_cas_from_xmi(f, typesystem=typesystem)

    # with open(xmlfile + ".json", 'w', encoding='utf-8') as out_f:
    #     out_f.write(json.dumps(json.loads(cas.to_json()), indent=2))

    tml = generateTimeML(cas)

    print(etree.tostring(tml, pretty_print=True, encoding="unicode"))


    with open(xmlfile + ".tml", 'w', encoding='utf-8') as out_f:
        out_f.write(etree.tostring(tml, pretty_print=True, xml_declaration=True, encoding="UTF-8").decode("utf-8"))
    result = validator.validateFile(xmlfile + ".tml", "xml-xsd")
    print("\n".join(result[1:]))
    with open("validation_report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(result[1:]))


    # print(json.dumps(json.loads(cas.to_json()), indent=2))
