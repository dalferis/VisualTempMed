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
# translate[<cas_tag>][<cas_attrib>][<cas_value>] = <tml_value>
# Example:
# translate["EVENT"]["eventType"]["N/A"] returns "OCCURRENCE"
translate = {
    "EVENT": {
        # eventType --> class
        # class: OCCURRENCE, ASPECTUAL, REPORTING, PERCEPTION, I_STATE, I_ACTION, STATE
        "eventType": {
            "N/A": "OCCURRENCE",
            "ASPECTUAL": "ASPECTUAL",
            "EVIDENTIAL": "REPORTING"
        },
        # docTimeRel --> tense/aspect/pos
        # tense: PRESENT, PAST, FUTURE, INFINITIVE, PRESPART, PASTPART, NONE
        # aspect: PROGRESSIVE, PERFECTIVE, PERFECTIVE_PROGRESSIVE, NONE
        # pos: VERB, NOUN, ADJECTIVE, PREP, OTHER
        "docTimeRel": {
            "BEFORE": {"tense":"PAST","aspect":"PERFECTIVE","pos":"OTHER"},
            "AFTER": {"tense":"FUTURE","aspect":"PERFECTIVE","pos":"OTHER"},
            "CONTAINS": {"tense":"PRESENT","aspect":"PROGRESSIVE","pos":"OTHER"},
            "IS-CONTAINED": {"tense":"PRESENT","aspect":"NONE","pos":"OTHER"},
            "OVERLAP": {"tense":"PRESENT","aspect":"NONE","pos":"OTHER"}
        }
    },
    "TIMEX3": {
        "timex3Class": {
            "DATE": "DATE",
            "TIME": "TIME",
            "DURATION": "DURATION",
            "QUANTIFIER": "DURATION",
            "PREPOSTEXP": "DATE",
            "SET": "SET"
        }
    },
    "TLINK": {
        "role": {
            "BEFORE": "BEFORE",
            "CONTAINS": "INCLUDES",
            "SIMULTANEOUS": "SIMULTANEOUS",
            "OVERLAP": "DURING",
            "BEGINS-ON": "BEGINS",
            "ENDS-ON": "ENDS"
        }
    },
    "ALINK": {
        "role": {
            "CONTINUES": "CONTINUES",
            "INITIATES": "INITIATES",
            "TERMINATES": "TERMINATES"
        }
    }
}

def createEvent(event, cas_text, cas_tail):
    atrib = translate["EVENT"]["docTimeRel"][event["docTimeRel"]]
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
                "tense": atrib["tense"],
                "aspect": atrib["aspect"],
                #"pos": atrib["pos"],
                "polarity": event["polarity"]
                #"cardinality": "",
                #"modality": ""
            }
        },
    }

    links = []
    for link in event.TLINK.elements:
        new_link = {
            "tag": "TLINK",
            "cas_id": event.xmiID,
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
        links.append(new_link)
    for link in event.ALINK.elements:
        new_link = {
            "tag": "ALINK",
            "cas_id": event.xmiID,
            "cas_target_id": link.target.xmiID,
            "attrib": {
                "lid": ""
            }
        }
        if link.type.name == "webanno.custom.TIMEX3TimexLinkLink":
            new_link["attrib"]["timeID"] = ""
        elif link.type.name == "webanno.custom.EVENTALINKLink":
            new_link["attrib"]["eventInstanceID"] = ""
        new_link["attrib"]["relType"] = translate["ALINK"]["role"][link.role]
        if link.target.type.name == "webanno.custom.TIMEX3":
            new_link["attrib"]["relatedToTime"] = ""
        elif link.target.type.name == "webanno.custom.EVENT":
            new_link["attrib"]["relatedToEventInstance"] = ""
        links.append(new_link)
    return [new_event] + links

def createTimex3(timex3, cas_text, cas_tail):
    new_timex3 = {
        "tag": "TIMEX3",
        "cas_id": timex3.xmiID,
        "attrib": {
            "tid": "",
            "type": translate["TIMEX3"]["timex3Class"][timex3.timex3Class],
            "value": timex3.value,
            "temporalFunction": "false"
        },
        "text": cas_text,
        "tail": cas_tail,
    }

    links = []
    for link in timex3.timexLink.elements:
        new_link = {
            "tag": "TLINK",
            "cas_id": timex3.xmiID,
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
        links.append(new_link)

    # Special cases
    extra_links = []
    if timex3.timex3Class == "PREPOSTEXP":
        for link in timex3.timexLink.elements:
            new_timex3["attrib"]["value"] = "PRESENT_REF"
            new_link = {
                "tag": "TLINK",
                "cas_id": link.target.xmiID,
                "cas_target_id": timex3.xmiID,
                "attrib": {
                    "lid": "",
                    "eventInstanceID": "",
                    "relType": "AFTER",
                    "relatedToTime": ""
                }
            }
            extra_links.append(new_link)

    return [new_timex3] + links + extra_links

def assignId(tml_elements):
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
            event_count += 1
        elif element["tag"] == "TIMEX3":
            element["attrib"]["tid"] = f"t{timex3_count}"
            id_map[element["cas_id"]] = element["attrib"]["tid"]
            timex3_count += 1
        elif element["tag"] == "TLINK" or element["tag"] == "ALINK":
            element["attrib"]["lid"] = f"l{link_count}"
            link_count += 1
    for link in tml_elements:
        if link["tag"] == "TLINK" or link["tag"] == "ALINK":
            # Source
            if "timeID" in link["attrib"]:
                link["attrib"]["timeID"] = id_map.get(link["cas_id"], "")
            elif "eventInstanceID" in link["attrib"]:
                link["attrib"]["eventInstanceID"] = id_map.get(link["cas_id"], "")
            # Target
            if "relatedToTime" in link["attrib"]:
                link["attrib"]["relatedToTime"] = id_map.get(link["cas_target_id"], "")
            elif "relatedToEventInstance" in link["attrib"]:
                link["attrib"]["relatedToEventInstance"] = id_map.get(link["cas_target_id"], "")

def sortTmlElements(element):
    if element["tag"] == "EVENT" or element["tag"] == "TIMEX3":
        return 0
    elif element["tag"] == "TLINK":
        return 1
    elif element["tag"] == "ALINK":
        return 2
    return 1000

def writeTml(root, initial_text, tml_elements):
    tml_elements.sort(key=sortTmlElements)
    tml_text = etree.SubElement(root, "TEXT")
    tml_text.text = initial_text
    for element in tml_elements:
        if element["tag"] == 'EVENT' or element["tag"] == "TIMEX3":
            event = etree.SubElement(tml_text, element["tag"], attrib=element["attrib"])
            event.text = element["text"]
            event.tail = element["tail"]
            if element["tag"] == "EVENT":
                etree.SubElement(root, element["instance"]["tag"], attrib=element["instance"]["attrib"])
        elif element["tag"] == "TLINK" or element["tag"] == "ALINK":
            etree.SubElement(root, element["tag"], attrib=element["attrib"])

def getDocId(cas):
    dmd_list = cas.select("de.tudarmstadt.ukp.dkpro.core.api.metadata.type.DocumentMetaData")
    if not dmd_list:
        return "UNKNOWN_DOCID"
    return dmd_list[0].documentId

def generateTimeML(cas):
    etree.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root = etree.Element("TimeML")
    root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", "TimeML_1.2.1.xsd")
    etree.SubElement(root, "DOCID").text = getDocId(cas)

    cas_text = cas.sofa_string
    cas_elements = list(cas.select("webanno.custom.EVENT")) + list(cas.select("webanno.custom.TIMEX3")) + [{"begin": len(cas_text)}]
    cas_elements.sort(key=lambda e: e["begin"])

    tml_elements = []

    for i, element in enumerate(cas_elements[:-1]):
        if element.type.name == "webanno.custom.EVENT":
            tml_elements.extend(createEvent(element, cas_text[element["begin"]:element["end"]], cas_text[element["end"]:cas_elements[i+1]["begin"]]))
        elif element.type.name == "webanno.custom.TIMEX3":
            tml_elements.extend(createTimex3(element, cas_text[element["begin"]:element["end"]], cas_text[element["end"]:cas_elements[i+1]["begin"]]))

    assignId(tml_elements)
    writeTml(root, cas_text[0:cas_elements[0]["begin"]], tml_elements)

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
