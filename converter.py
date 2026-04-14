from cassis import *
from lxml import etree
import json
import validator
from dateutil import parser
from dateutil.parser import ParserError

def translateEvent(event, cas_text, cas_tail):
    new_event =  {
        "tag": "EVENT",
        "cas_id": event.xmiID,
        "attrib": { "eid": "", "class": "" },
        "text": cas_text,
        "tail": cas_tail,
        "instance": {
            "tag": "MAKEINSTANCE",
            "attrib": { "eiid": "", "eventID": "", "tense": "NONE", "aspect": "NONE", "pos": "OTHER" }
        }
    }
    links = []
    # docTimeRel values
    if hasattr(event, "docTimeRel"):
        new_link = {
            "tag": "TLINK",
            "cas_id": event.xmiID,
            "cas_target_id": 0,
            "attrib": { "lid": "", "eventInstanceID": "", "relatedToTime": "", "relType": "" },
        }
        new_event["attrib"]["class"] = "OCCURRENCE"
        if event["docTimeRel"] == "BEFORE":
            new_link["attrib"]["relType"] = "BEFORE"
        elif event["docTimeRel"] == "AFTER":
            new_link["attrib"]["relType"] = "AFTER"
        elif event["docTimeRel"] == "CONTAINS":
            new_link["attrib"]["relType"] = "INCLUDES"
        elif event["docTimeRel"] == "IS-CONTAINED":
            new_link["attrib"]["relType"] = "IS_INCLUDED"
        elif event["docTimeRel"] == "OVERLAP":
            new_link["attrib"]["relType"] = "SIMULTANEOUS"
        links.append(new_link)
    # eventType values
    if hasattr(event, "eventType"):
        if event["eventType"] == "N/A":
            new_event["attrib"]["class"] = "OCCURRENCE"
        elif event["eventType"] == "ASPECTUAL":
            new_event["attrib"]["class"] = "ASPECTUAL"
        elif event["eventType"] == "EVIDENTIAL":
            new_event["attrib"]["class"] = "REPORTING"
    # degree values
    if hasattr(event, "degree"):
        if event["degree"] == "MOST":
            new_event["instance"]["attrib"]["modality"] = "MOST"
        elif event["degree"] == "LITTLE":
            new_event["instance"]["attrib"]["modality"] = "LITTLE"
    # contextualModality values
    # if hasattr(event, "contextualModality"):
    #     if event["contextualModality"] == "ACTUAL":
    #         new_event["instance"]["attrib"]["modality"] = "ACTUAL"
    #     elif event["contextualModality"] == "HYPOTHETICAL-IF":
    #         new_event["instance"]["attrib"]["modality"] = "IF"
    #     elif event["contextualModality"] == "HYPOTHETICAL-OTHER":
    #         new_event["instance"]["attrib"]["modality"] = "POSSIBLE"
    #     elif event["contextualModality"] == "HEDGED":
    #         new_event["instance"]["attrib"]["modality"] = "HEDGED"
    #     elif event["contextualModality"] == "GENERIC":
    #         new_event["instance"]["attrib"]["modality"] = "GENERIC"
    # contextualAspect values
    if hasattr(event, "contextualAspect"):
        if event["contextualAspect"] == "NOVEL":
            new_event["instance"]["attrib"]["aspect"] = "NONE"
        elif event["contextualAspect"] == "INTERMITTENT":
            new_event["instance"]["attrib"]["aspect"] = "PROGRESSIVE"
    # permanence values
    # if hasattr(event, "permanence"):
    #     if event["permanence"] == "FINITE":
    #         new_event["instance"]["attrib"]["modality"] = "FINITE"
    #     elif event["permanence"] == "PERMANENT":
    #         new_event["instance"]["attrib"]["modality"] = "PERMANENT"
    # polarity values
    if hasattr(event, "polarity"):
        new_event["instance"]["attrib"]["polarity"] = event["polarity"]
    # tlinks
    for link in event.TLINK.elements:
        new_link = {
            "tag": "TLINK",
            "cas_id": event.xmiID,
            "cas_target_id": link.target.xmiID,
            "attrib": { "lid": "" }
        }
        if link.type.name == "webanno.custom.TIMEX3TimexLinkLink":
            new_link["attrib"]["timeID"] = ""
        elif link.type.name == "webanno.custom.EVENTTLINKLink":
            new_link["attrib"]["eventInstanceID"] = ""
        if link.target.type.name == "webanno.custom.TIMEX3":
            new_link["attrib"]["relatedToTime"] = ""
        elif link.target.type.name == "webanno.custom.EVENT":
            new_link["attrib"]["relatedToEventInstance"] = ""
        # role values
        if link.role == "BEFORE":
            new_link["attrib"]["relType"] = "BEFORE"
        elif link.role == "OVERLAP":
            new_link["attrib"]["relType"] = "SIMULTANEOUS"
        elif link.role == "CONTAINS":
            new_link["attrib"]["relType"] = "INCLUDES"
        elif link.role == "BEGINS-ON":
            new_link["attrib"]["relType"] = "BEGUN_BY"
        elif link.role == "ENDS-ON":
            new_link["attrib"]["relType"] = "ENDED_BY"
        elif link.role == "SIMULTANEOUS":
            new_link["attrib"]["relType"] = "SIMULTANEOUS"

        links.append(new_link)
    # alinks
    for link in event.ALINK.elements:
        new_link = {
            "tag": "ALINK",
            "cas_id": event.xmiID,
            "cas_target_id": link.target.xmiID,
            "attrib": { "lid": "" }
        }
        if link.type.name == "webanno.custom.TIMEX3TimexLinkLink":
            new_link["attrib"]["timeID"] = ""
        elif link.type.name == "webanno.custom.EVENTALINKLink":
            new_link["attrib"]["eventInstanceID"] = ""
        if link.target.type.name == "webanno.custom.TIMEX3":
            new_link["attrib"]["relatedToTime"] = ""
        elif link.target.type.name == "webanno.custom.EVENT":
            new_link["attrib"]["relatedToEventInstance"] = ""
        # role values
        new_link["attrib"]["relType"] = link.role
        
        links.append(new_link)

    return [new_event] + links

def translateTimex3(timex3, cas_text, cas_tail):
    new_timex3 = {
        "tag": "TIMEX3",
        "cas_id": timex3.xmiID,
        "attrib": { "tid": "", "type": "", "value": "X" if timex3.value.lower()=="no_value" else timex3.value },
        "text": cas_text,
        "tail": cas_tail,
    }
    links = []
    # timex3Class values
    if hasattr(timex3, "timex3Class"):
        if timex3.timex3Class == "DATE":
            new_timex3["attrib"]["type"] = "DATE"
            new_timex3["attrib"]["temporalFunction"] = "true"
        elif timex3.timex3Class == "TIME":
            new_timex3["attrib"]["type"] = "TIME"
            new_timex3["attrib"]["temporalFunction"] = "true"
        elif timex3.timex3Class == "DURATION":
            new_timex3["attrib"]["type"] = "DURATION"
            new_timex3["attrib"]["temporalFunction"] = "true"
        elif timex3.timex3Class == "QUANTIFIER":
            new_timex3["attrib"]["type"] = "SET"
            new_timex3["attrib"]["temporalFunction"] = "true"
        elif timex3.timex3Class == "SET":
            new_timex3["attrib"]["type"] = "SET"
            new_timex3["attrib"]["temporalFunction"] = "true"
        elif timex3.timex3Class == "PREPOSTEXP":
            new_timex3["attrib"]["type"] = "DATE"
            new_timex3["attrib"]["temporalFunction"] = "true"
    # functionInDocument values
    if hasattr(timex3, "functionInDocument"):
        if timex3.functionInDocument == "DOCTIME":
            new_timex3["attrib"]["functionInDocument"] = "CREATION_TIME"
        elif timex3.functionInDocument == "SECTIONTIME":
            new_timex3["attrib"]["functionInDocument"] = "CREATION_TIME"
    # links
    for link in timex3.timexLink.elements:
        new_link = {
            "tag": "TLINK",
            "cas_id": timex3.xmiID,
            "cas_target_id": link.target.xmiID,
            "attrib": { "lid": "" }
        }
        if link.type.name == "webanno.custom.TIMEX3TimexLinkLink":
            new_link["attrib"]["timeID"] = ""
        elif link.type.name == "webanno.custom.EVENTTLINKLink":
            new_link["attrib"]["eventInstanceID"] = ""
        if link.target.type.name == "webanno.custom.TIMEX3":
            new_link["attrib"]["relatedToTime"] = ""
        elif link.target.type.name == "webanno.custom.EVENT":
            new_link["attrib"]["relatedToEventInstance"] = ""
        # role values
        if link.role == "BEFORE":
            new_link["attrib"]["relType"] = "BEFORE"
        elif link.role == "OVERLAP":
            new_link["attrib"]["relType"] = "SIMULTANEOUS"
        elif link.role == "CONTAINS":
            new_link["attrib"]["relType"] = "INCLUDES"
        elif link.role == "BEGINS-ON":
            new_link["attrib"]["relType"] = "BEGUN_BY"
        elif link.role == "ENDS-ON":
            new_link["attrib"]["relType"] = "ENDED_BY"
        elif link.role == "SIMULTANEOUS":
            new_link["attrib"]["relType"] = "SIMULTANEOUS"

        links.append(new_link)

    return [new_timex3] + links

def assignId(tml_elements):
    link_count = 1
    event_count = 1
    timex3_count = 1
    id_map = {}
    id_map[0] = "t0"  # DCT ID
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

def generateTimeML(cas):
    cas_text = cas.sofa_string
    cas_elements = list(cas.select("webanno.custom.EVENT")) + list(cas.select("webanno.custom.TIMEX3")) + [{"begin": len(cas_text)}]
    cas_elements.sort(key=lambda e: e["begin"])

    tml_elements = []

    # TML namespace and schema declaration
    etree.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root = etree.Element("TimeML")
    root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", "TimeML_1.2.1.xsd")

    # TML header information
    cas_metadata = cas.select("de.tudarmstadt.ukp.dkpro.core.api.metadata.type.DocumentMetaData") + cas.select("webanno.custom.METADATA")
    for meta in cas_metadata:
        if hasattr(meta, "documentId"):
            etree.SubElement(root, "DOCID").text = meta.documentId
        if hasattr(meta, "docTime"):
            dct = etree.SubElement(root, "DD")
            try:
                dct_parsed = parser.parse(meta.docTime)
                etree.SubElement(dct, "TIMEX3", attrib={"tid": "t0", "type": "DATE", "value": dct_parsed.isoformat(), "functionInDocument": "CREATION_TIME", "temporalFunction": "false"}).text = meta.docTime
            except (ParserError, ValueError):
                etree.SubElement(dct, "TIMEX3", attrib={"tid": "t0", "type": "DATE", "value": "NO_VALUE", "functionInDocument": "CREATION_TIME", "temporalFunction": "false"}).text = meta.docTime
        if hasattr(meta, "language"):
            etree.SubElement(root, "LANGUAGE").text = meta.language

    # TML elements
    # 1. Generate "pre-TML" elements for each CAS element, including text and tail
    for i, element in enumerate(cas_elements[:-1]):
        if element.type.name == "webanno.custom.EVENT":
            tml_elements.extend(translateEvent(element, cas_text[element["begin"]:element["end"]], cas_text[element["end"]:cas_elements[i+1]["begin"]]))
        elif element.type.name == "webanno.custom.TIMEX3":
            tml_elements.extend(translateTimex3(element, cas_text[element["begin"]:element["end"]], cas_text[element["end"]:cas_elements[i+1]["begin"]]))
    # 2. Assign IDs to "pre-TML" elements and update links with source and target IDs
    assignId(tml_elements)
    # 3. Sort "pre-TML" elements 
    tml_elements.sort(key=sortTmlElements)
    # 4. Construct TML XML with text, events, timex3s, and links
    tml_text = etree.SubElement(root, "TEXT")
    tml_text.text = cas_text[0:cas_elements[0]["begin"]]
    for element in tml_elements:
        if element["tag"] == 'EVENT' or element["tag"] == "TIMEX3":
            event = etree.SubElement(tml_text, element["tag"], attrib=element["attrib"])
            event.text = element["text"]
            event.tail = element["tail"]
            if element["tag"] == "EVENT":
                etree.SubElement(root, element["instance"]["tag"], attrib=element["instance"]["attrib"])
        elif element["tag"] == "TLINK" or element["tag"] == "ALINK":
            etree.SubElement(root, element["tag"], attrib=element["attrib"])

    return root

def convertFile(xmlfile: str, typesystemfile: str):
    with open(typesystemfile, 'rb') as f:
        typesystem = load_typesystem(f)

    with open(xmlfile, 'rb') as f:
        cas = load_cas_from_xmi(f, typesystem=typesystem)

    # with open(xmlfile + ".json", 'w', encoding='utf-8') as out_f:
    #     out_f.write(json.dumps(json.loads(cas.to_json()), indent=2))

    tml = generateTimeML(cas)

    #print(etree.tostring(tml, pretty_print=True, encoding="unicode"))

    with open(xmlfile + ".tml", 'w', encoding='utf-8') as out_f:
        out_f.write(etree.tostring(tml, pretty_print=True, xml_declaration=True, encoding="UTF-8").decode("utf-8"))
    result = validator.validateFile(xmlfile + ".tml", "xml-xsd")
    print("\n".join(result[1:]))
    with open("validation_report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(result[1:]))

    # print(json.dumps(json.loads(cas.to_json()), indent=2))
