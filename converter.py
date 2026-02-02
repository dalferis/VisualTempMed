#from asyncio import events
#from os import eventfd
from asyncio import events
from math import e
import re
from tkinter import W
import attr
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
translate["TIMEX3"] = {
    "timex3Class": {
        "DATE": "DATE",
        "TIME": "TIME",
        "DURATION": "DURATION",
        "QUANTIFIER": "DURATION",
        "PREPOSTEXP": "DATE",
        "SET": "SET"
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
translate["ALINK"] = {
    "role": {
        "CONTINUES": "CONTINUES",
        "INITIATES": "INITIATES",
        "TERMINATES": "TERMINATES"
    }
}

def get_docid(cas):
    dmd_list = cas.select("de.tudarmstadt.ukp.dkpro.core.api.metadata.type.DocumentMetaData")
    if not dmd_list:
        return "UNKNOWN_DOCID"
    return dmd_list[0].documentId

def create_event(event, cas_text, cas_tail):
    new_event =  {
        "tag": "EVENT",
        "cas_id": event.xmiID,
        "attrib": {
            "eid": "",
            "class": translate["EVENT"]["eventType"][event["eventType"]],
        },
        "text": cas_text,
        "tail": cas_tail,
        "instance": {
            "tag": "MAKEINSTANCE",
            "attrib": {
                "eiid": "",
                "eventID": "",
                "pos": "OTHER",
                "tense": translate["EVENT"]["docTimeRel"][event["docTimeRel"]],
                "aspect": "NONE",
                "polarity": event["polarity"]
                #"cardinality": "",
                #"modality": ""
            }
        },
        "tlinks": [],
        "alinks": []
    }
    for link in event.TLINK.elements:
        new_link = {
            "tag": "TLINK",
            "cas_target_id": link.target.xmiID,
            "attrib": {
                "lid": ""
            }
        }
        if link.type.name == "webanno.custom.TIMEX3TimexLinkLink":
            new_link["attrib"]["timeID"] = ""
        elif link.type.name == "webanno.custom.EVENTTLINKLink":
            new_link["attrib"]["eventInstanceID"] = ""
        new_link["attrib"]["relType"] = translate["TLINK"]["role"][link.role]
        if link.target.type.name == "webanno.custom.TIMEX3":
            new_link["attrib"]["relatedToTime"] = ""
        elif link.target.type.name == "webanno.custom.EVENT":
            new_link["attrib"]["relatedToEventInstance"] = ""
        new_event["tlinks"].append(new_link)
    for link in event.ALINK.elements:
        new_link = {
            "tag": "ALINK",
            "cas_target_id": link.target.xmiID,
            "attrib": {
                "lid": ""
            }
        }
        if link.type.name == "webanno.custom.TIMEX3TimexLinkLink":
            new_link["attrib"]["timeID"] = ""
        elif link.type.name == "webanno.custom.EVENTTLINKLink":
            new_link["attrib"]["eventInstanceID"] = ""
        new_link["attrib"]["relType"] = translate["ALINK"]["role"][link.role]
        if link.target.type.name == "webanno.custom.TIMEX3":
            new_link["attrib"]["relatedToTime"] = ""
        elif link.target.type.name == "webanno.custom.EVENT":
            new_link["attrib"]["relatedToEventInstance"] = ""
        new_event["alinks"].append(new_link)
    return [new_event]

def create_timex3(event, cas_text, cas_tail):
    new_timex3 = {
        "tag": "TIMEX3",
        "cas_id": event.xmiID,
        "attrib": {
            "tid": "",
            "type": translate["TIMEX3"]["timex3Class"][event.timex3Class],
            "value": event.value
        },
        "text": cas_text,
        "tail": cas_tail,
        "tlinks": []
    }

    if event.timex3Class == "PREPOSTEXP":
        new_timex3["attrib"]["value"] = "PRESENT_REF"
        new_link = {
            "tag": "TLINK",
            "cas_target_id": event.xmiID,
            "attrib": {
                "lid": "",
                "eventInstanceID": "", # debe apuntar al evento anterior
                "relType": "AFTER",
                "relatedToTime": ""
            }
        }
        new_timex3["tlinks"].append(new_link)

    for link in event.timexLink.elements:
        new_link = {
            "tag": "TLINK",
            "cas_target_id": link.target.xmiID,
            "attrib": {
                "lid": ""
            }
        }
        if link.type.name == "webanno.custom.TIMEX3TimexLinkLink":
            new_link["attrib"]["timeID"] = ""
        elif link.type.name == "webanno.custom.EVENTTLINKLink":
            new_link["attrib"]["eventInstanceID"] = ""
        new_link["attrib"]["relType"] = translate["TLINK"]["role"][link.role]
        if link.target.type.name == "webanno.custom.TIMEX3":
            new_link["attrib"]["relatedToTime"] = ""
        elif link.target.type.name == "webanno.custom.EVENT":
            new_link["attrib"]["relatedToEventInstance"] = ""
        new_timex3["tlinks"].append(new_link)
    return [new_timex3]

def assign_id(tml_elements):
    link_count = 1
    event_count = 1
    timex3_count = 1
    id_map = {}
    for element in tml_elements:
        if element["tag"] == "EVENT":
            element["attrib"]["eid"] = f"e{event_count}"
            element["instance"]["attrib"]["eiid"] = f"ei{event_count}"
            element["instance"]["attrib"]["eventID"] = f"e{event_count}"
            id_map[element["cas_id"]] = element["instance"]["attrib"]["eiid"]
            for link in element["tlinks"]:
                link["attrib"]["lid"] = f"l{link_count}"
                link_count += 1
            for link in element["alinks"]:
                link["attrib"]["lid"] = f"l{link_count}"
                link_count += 1
            event_count += 1
        elif element["tag"] == "TIMEX3":
            element["attrib"]["tid"] = f"t{timex3_count}"
            id_map[element["cas_id"]] = element["attrib"]["tid"]
            for link in element["tlinks"]:
                link["attrib"]["lid"] = f"l{link_count}"
                link_count += 1
            timex3_count += 1
    for element in tml_elements:
        for link in element.get("tlinks", []) + element.get("alinks", []):
            # Source
            if "timeID" in link["attrib"]:
                link["attrib"]["timeID"] = element["attrib"]["tid"]
            elif "eventInstanceID" in link["attrib"]:
                link["attrib"]["eventInstanceID"] = element["instance"]["attrib"]["eiid"]
            # Target
            if "relatedToTime" in link["attrib"]:
                link["attrib"]["relatedToTime"] = id_map.get(link["cas_target_id"], "")
            elif "relatedToEventInstance" in link["attrib"]:
                link["attrib"]["relatedToEventInstance"] = id_map.get(link["cas_target_id"], "")
            pass

def write_tml(root, initial_text, tml_elements):
    tml_text = etree.SubElement(root, "TEXT")
    tml_text.text = initial_text
    for element in tml_elements:
        event = etree.SubElement(tml_text, element["tag"], attrib=element["attrib"])
        event.text = element["text"]
        event.tail = element["tail"]
        if element["tag"] == "EVENT":
            etree.SubElement(root, element["instance"]["tag"], attrib=element["instance"]["attrib"])
    for element in tml_elements:
        for link in element.get("tlinks", []):
            etree.SubElement(root, link["tag"], attrib=link["attrib"])
        for link in element.get("alinks", []):
            etree.SubElement(root, link["tag"], attrib=link["attrib"])

def event(root, cas):
    cas_text = cas.sofa_string
    cas_elements = list(cas.select("webanno.custom.EVENT")) + list(cas.select("webanno.custom.TIMEX3")) + [{"begin": len(cas_text)}]
    cas_elements.sort(key=lambda e: e["begin"])

    tml_elements = []

    for i, element in enumerate(cas_elements[:-1]):
        if element.type.name == "webanno.custom.EVENT":
            tml_elements.extend(create_event(element, cas_text[element["begin"]:element["end"]], cas_text[element["end"]:cas_elements[i+1]["begin"]]))
        elif element.type.name == "webanno.custom.TIMEX3":
            tml_elements.extend(create_timex3(element, cas_text[element["begin"]:element["end"]], cas_text[element["end"]:cas_elements[i+1]["begin"]]))

    assign_id(tml_elements)
    write_tml(root, cas_text[0:cas_elements[0]["begin"]], tml_elements)


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
