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

def create_event(parent, event, eid, cas_text, cas_tail):
    tml_event = etree.SubElement(parent, "EVENT",
        attrib = {
            "eid":eid,
            "class":translate["EVENT"]["eventType"][event["eventType"]],
        }
    )
    tml_event.text = cas_text
    tml_event.tail = cas_tail

def create_makeinstance(parent, event, eiid, eid):
    etree.SubElement(parent, "MAKEINSTANCE",
        attrib = {
            "eiid":eiid,
            "eventID":eid,
            "pos":"OTHER",
            "tense":translate["EVENT"]["docTimeRel"][event["docTimeRel"]],
            "aspect":"NONE",
            "polarity":event["polarity"]
            #"cardinality":"",
            #"modality":""
        }
    )

def create_timex3(parent, event, tid, cas_text, cas_tail):
    tml_timex3 = etree.SubElement(parent, "TIMEX3",
        attrib = {
            "tid":tid,
            "type":event.timex3Class,
            "value":event.value
        }
    )
    tml_timex3.text = cas_text
    tml_timex3.tail = cas_tail

def create_tlink_attrib(tlink, lid, eid, target_id):
    attrib = {
        "lid":lid
    }
    if tlink.type.name == "webanno.custom.TIMEX3TimexLinkLink":
        attrib["timeID"] = eid
    elif tlink.type.name == "webanno.custom.EVENTTLINKLink":
        attrib["eventInstanceID"] = eid
    attrib["relType"] = translate["TLINK"]["role"][tlink.role]
    if tlink.target.type.name == "webanno.custom.TIMEX3":
        attrib["relatedToTime"] = target_id
    elif tlink.target.type.name == "webanno.custom.EVENT":
        attrib["relatedToEventInstance"] = target_id
    return attrib

def create_tlink(root, attrib, event_id_map):
    if ("relatedToTime" in attrib):
        if attrib["relatedToTime"] in event_id_map:
            attrib["relatedToTime"] = event_id_map[attrib["relatedToTime"]]
            etree.SubElement(root, "TLINK", attrib=attrib)
    elif ("relatedToEventInstance" in attrib):
        if attrib["relatedToEventInstance"] in event_id_map:
            attrib["relatedToEventInstance"] = event_id_map[attrib["relatedToEventInstance"]]
            etree.SubElement(root, "TLINK", attrib=attrib)

def event(root, cas):
    cas_text = cas.sofa_string
    cas_elements = list(cas.select("webanno.custom.EVENT")) + list(cas.select("webanno.custom.TIMEX3")) + [{"begin": len(cas_text)}]
    cas_elements = sorted(cas_elements, key=lambda e: e["begin"])

    tml_text = etree.SubElement(root, "TEXT")
    tml_text.text = cas_text[0:cas_elements[0]["begin"]]
    tml_tlink_attrib = []

    element_id_map = {}

    tlink_count = 1
    event_count = 1
    timex3_count = 1
    for element in cas_elements[:-1]:
        ##### Write EVENTs #####
        if element.type.name == "webanno.custom.EVENT":
            create_event(tml_text, element, f"e{event_count}", cas_text[element["begin"]:element["end"]], cas_text[element["end"]:cas_elements[event_count+timex3_count-1]["begin"]])
            ##### Write MAKEINSTANCEs #####
            create_makeinstance(root, element, f"ei{event_count}", f"e{event_count}")
            element_id_map[element.xmiID] = f"ei{event_count}"
            ##### Prepare TLINKs #####
            for tlink in element.TLINK.elements:
                tml_tlink_attrib.append(create_tlink_attrib(tlink, f"l{tlink_count}", f"ei{event_count}", tlink.target.xmiID))
                tlink_count += 1
            event_count += 1
        elif element.type.name == "webanno.custom.TIMEX3":
            create_timex3(tml_text, element, f"t{timex3_count}", cas_text[element["begin"]:element["end"]], cas_text[element["end"]:cas_elements[event_count+timex3_count-1]["begin"]])
            element_id_map[element.xmiID] = f"t{timex3_count}"
            for tlink in element.timexLink.elements:
                tml_tlink_attrib.append(create_tlink_attrib(tlink, f"l{tlink_count}", f"t{timex3_count}", tlink.target.xmiID))
                tlink_count += 1
            timex3_count += 1
    ##### Write TLINKs #####
    for attrib in tml_tlink_attrib:
        create_tlink(root, attrib, element_id_map)

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
