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
            "tail": cas_tail
        }
    new_makeinstance = {
            "tag": "MAKEINSTANCE",
            "cas_event_id": event.xmiID,
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
        }
    new_links = []
    for link in event.TLINK.elements:
        new_link = {
                "tag": "TLINK",
                "cas_id": link.target.xmiID,
                "cas_source_id": event.xmiID,
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
        new_links.append(new_link)
    for link in event.ALINK.elements:
        new_link = {
                "tag": "ALINK",
                "cas_id": link.target.xmiID,
                "cas_source_id": event.xmiID,
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
        new_links.append(new_link)
    return [new_event, new_makeinstance] + new_links

def create_timex3(event, cas_text, cas_tail):
    element = {
        "tag": "TIMEX3",
        "cas_id": event.xmiID,
        "attrib": {
            "tid": "",
            "type": translate["TIMEX3"]["timex3Class"][event.timex3Class]
        },
        "text": cas_text,
        "tail": cas_tail
    }
    if event.timex3Class != "PREPOSTEXP":
        element["attrib"]["value"] = event.value
    else:
        element["attrib"]["value"] = "PRESENT_REF"
    new_links = []
    for link in event.timexLink.elements:
        new_link = {
                "tag": "TLINK",
                "cas_id": link.target.xmiID,
                "cas_source_id": event.xmiID,
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
        new_links.append(new_link)
    return [element] + new_links

# def create_tlink_attrib(tlink):
#     attrib = {
#         "lid": ""
#     }
#     if tlink.type.name == "webanno.custom.TIMEX3TimexLinkLink":
#         attrib["timeID"] = ""
#     elif tlink.type.name == "webanno.custom.EVENTTLINKLink":
#         attrib["eventInstanceID"] = ""
#     attrib["relType"] = translate["TLINK"]["role"][tlink.role]
#     if tlink.target.type.name == "webanno.custom.TIMEX3":
#         attrib["relatedToTime"] = ""
#     elif tlink.target.type.name == "webanno.custom.EVENT":
#         attrib["relatedToEventInstance"] = ""
#     return [{
#         "tag": "TLINK",
#         "cas_id": tlink.target.xmiID,
#         "attrib": attrib
#     }]

# def create_tlink(root, attrib, event_id_map):
#     if ("relatedToTime" in attrib):
#         if attrib["relatedToTime"] in event_id_map:
#             attrib["relatedToTime"] = event_id_map[attrib["relatedToTime"]]
#             etree.SubElement(root, "TLINK", attrib=attrib)
#     elif ("relatedToEventInstance" in attrib):
#         if attrib["relatedToEventInstance"] in event_id_map:
#             attrib["relatedToEventInstance"] = event_id_map[attrib["relatedToEventInstance"]]
#             etree.SubElement(root, "TLINK", attrib=attrib)

# def create_alink_attrib(alink):
#     attrib = {
#         "lid": ""
#     }
#     if alink.type.name == "webanno.custom.TIMEX3TimexLinkLink":
#         attrib["timeID"] = ""
#     elif alink.type.name == "webanno.custom.EVENTALINKLink":
#         attrib["eventInstanceID"] = ""
#     attrib["relType"] = translate["ALINK"]["role"][alink.role]
#     if alink.target.type.name == "webanno.custom.TIMEX3":
#         attrib["relatedToTime"] = ""
#     elif alink.target.type.name == "webanno.custom.EVENT":
#         attrib["relatedToEventInstance"] = ""
#     return [{
#         "tag": "ALINK",
#         "cas_id": alink.target.xmiID,
#         "attrib": attrib
#     }]

# def create_alink(root, attrib, event_id_map):
#     if ("relatedToTime" in attrib):
#         if attrib["relatedToTime"] in event_id_map:
#             attrib["relatedToTime"] = event_id_map[attrib["relatedToTime"]]
#             etree.SubElement(root, "ALINK", attrib=attrib)
#     elif ("relatedToEventInstance" in attrib):
#         if attrib["relatedToEventInstance"] in event_id_map:
#             attrib["relatedToEventInstance"] = event_id_map[attrib["relatedToEventInstance"]]
#             etree.SubElement(root, "ALINK", attrib=attrib)


def sort_elements(element):
    if element["tag"] == "EVENT":
        return int(element["attrib"]["eid"][1:]) + 0
    elif element["tag"] == "TIMEX3":
        return int(element["attrib"]["tid"][1:]) + 100000
    elif element["tag"] == "MAKEINSTANCE":
        return int(element["attrib"]["eiid"][2:]) + 2000000
    elif element["tag"] == "TLINK":
        return int(element["attrib"]["lid"][1:]) + 3000000
    elif element["tag"] == "ALINK":
        return int(element["attrib"]["lid"][1:]) + 4000000

def assign_id(tml_elements):
    link_count = 1
    event_count = 1
    makeinstance_count = 1
    timex3_count = 1
    id_map = {}
    for element in tml_elements:
        if element["tag"] == "EVENT":
            element["attrib"]["eid"] = f"e{event_count}"
            id_map[element["cas_id"]] = f"e{event_count}"
            event_count += 1
        elif element["tag"] == "MAKEINSTANCE":
            element["attrib"]["eiid"] = f"ei{makeinstance_count}"
            makeinstance_count += 1
        elif element["tag"] == "TIMEX3":
            element["attrib"]["tid"] = f"t{timex3_count}"
            id_map[element["cas_id"]] = f"t{timex3_count}"
            timex3_count += 1
        elif element["tag"] == "TLINK":
            element["attrib"]["lid"] = f"l{link_count}"
            link_count += 1
        elif element["tag"] == "ALINK":
            element["attrib"]["lid"] = f"l{link_count}"
            link_count += 1
    for element in tml_elements:
        if element["tag"] == "MAKEINSTANCE":
            element["attrib"]["eventID"] = id_map.get(element["cas_event_id"], "")
        elif element["tag"] == "TLINK":
            if "timeID" in element["attrib"]:
                element["attrib"]["timeID"] = id_map.get(element["cas_source_id"], "")
            elif "eventInstanceID" in element["attrib"]:
                element["attrib"]["eventInstanceID"] = id_map.get(element["cas_source_id"], "")
            if "relatedToTime" in element["attrib"]:
                element["attrib"]["relatedToTime"] = id_map.get(element["cas_source_id"], "")
            elif "relatedToEventInstance" in element["attrib"]:
                element["attrib"]["relatedToEventInstance"] = id_map.get(element["cas_source_id"], "")
        elif element["tag"] == "ALINK":
            if "timeID" in element["attrib"]:
                element["attrib"]["timeID"] = id_map.get(element["cas_source_id"], "")
            elif "eventInstanceID" in element["attrib"]:
                element["attrib"]["eventInstanceID"] = id_map.get(element["cas_source_id"], "")
            if "relatedToTime" in element["attrib"]:
                element["attrib"]["relatedToTime"] = id_map.get(element["cas_source_id"], "")
            elif "relatedToEventInstance" in element["attrib"]:
                element["attrib"]["relatedToEventInstance"] = id_map.get(element["cas_source_id"], "")

def write_tml(root, cas, tml_elements):
    tml_elements.sort(key=sort_elements)
    # cas_text = cas.sofa_string
    tml_text = etree.SubElement(root, "TEXT")
    tml_text.text = "Pepito" # cas_text[0:tml_elements[0]["begin"]]
    for element in tml_elements:
        if element["tag"] == "EVENT" or element["tag"] == "TIMEX3":
            event = etree.SubElement(tml_text, element["tag"], attrib=element["attrib"])
            event.text = element["text"]
            event.tail = element["tail"]
        else:
            etree.SubElement(root, element["tag"], attrib=element["attrib"])

def event(root, cas):
    cas_text = cas.sofa_string
    cas_elements = list(cas.select("webanno.custom.EVENT")) + list(cas.select("webanno.custom.TIMEX3")) + [{"begin": len(cas_text)}]
    cas_elements.sort(key=lambda e: e["begin"])

    # tml_text = etree.SubElement(root, "TEXT")
    # tml_text.text = cas_text[0:cas_elements[0]["begin"]]
    # tml_tlink_attrib = []
    # tml_alink_attrib = []
    tml_elements = []

    # element_id_map = {}

    # link_count = 1
    # event_count = 1
    # timex3_count = 1
    for i, element in enumerate(cas_elements[:-1]):
        if element.type.name == "webanno.custom.EVENT":
            tml_elements.extend(create_event(element, cas_text[element["begin"]:element["end"]], cas_text[element["end"]:cas_elements[i+1]["begin"]]))
            # tml_elements += create_event(element, f"e{event_count}", cas_text[element["begin"]:element["end"]], cas_text[element["end"]:cas_elements[event_count+timex3_count-1]["begin"]])
            # tml_elements += create_makeinstance(element, f"ei{event_count}", f"e{event_count}")
            # element_id_map[element.xmiID] = f"ei{event_count}"
            # for tlink in element.TLINK.elements:
            #     tml_elements.extend(create_tlink_attrib(tlink))
                # link_count += 1
            # for alink in element.ALINK.elements:
            #     tml_elements.extend(create_alink_attrib(alink))
                # link_count += 1
            # event_count += 1
        elif element.type.name == "webanno.custom.TIMEX3":
            tml_elements.extend(create_timex3(element, cas_text[element["begin"]:element["end"]], cas_text[element["end"]:cas_elements[i+1]["begin"]]))
            # element_id_map[element.xmiID] = f"t{timex3_count}"
            # for tlink in element.timexLink.elements:
            #     tml_elements.extend(create_tlink_attrib(tlink))
            #     link_count += 1
            # timex3_count += 1
    ##### Write elements #####
    assign_id(tml_elements)
    write_tml(root, cas, tml_elements)
    # for element in tml_elements:
    #     etree.SubElement(root, element["tag"], attrib=element["attrib"])
    # for attrib in tml_tlink_attrib:
    #     create_tlink(root, attrib, element_id_map)
    # for attrib in tml_alink_attrib:
    #     create_alink(root, attrib, element_id_map)

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
