from cassis import *
from lxml import etree
import json
import os
import re
import validator
from detector import FileFormat, detectFormat
from dateutil import parser
from dateutil.parser import ParserError

def _addE3cComment(attrib: dict, key: str, value: str):
    pair = f"e3c:{key}={value}"
    if attrib.get("comment"):
        attrib["comment"] = attrib["comment"] + "; " + pair
    else:
        attrib["comment"] = pair

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

    ### EVENT ATTRIBUTES ###
    # eventType values
    if hasattr(event, "eventType"):
        if event["eventType"] == "N/A":
            new_event["attrib"]["class"] = "OCCURRENCE" # default value
        elif event["eventType"] == "ASPECTUAL":
            new_event["attrib"]["class"] = "ASPECTUAL"  # direct
        elif event["eventType"] == "EVIDENTIAL":
            new_event["attrib"]["class"] = "REPORTING"  # equivalent

    ### LINK TO DOCUMENT CREATION TIME
    # docTimeRel values
    if hasattr(event, "docTimeRel"):
        new_link = {
            "tag": "TLINK",
            "cas_id": event.xmiID,
            "cas_target_id": 0,
            "attrib": { "lid": "", "eventInstanceID": "", "relatedToTime": "", "relType": "" },
        }
        if event["docTimeRel"] == "BEFORE":
            new_link["attrib"]["relType"] = "BEFORE"   # direct
        elif event["docTimeRel"] == "AFTER":
            new_link["attrib"]["relType"] = "AFTER"    # direct
        elif event["docTimeRel"] == "CONTAINS":
            new_link["attrib"]["relType"] = "INCLUDES" # equivalent
        elif event["docTimeRel"] == "IS-CONTAINED":
            new_link["attrib"]["relType"] = "IS_INCLUDED"  # equivalent
        elif event["docTimeRel"] == "OVERLAP":
            new_link["attrib"]["relType"] = "SIMULTANEOUS" # approximate
            _addE3cComment(new_link["attrib"], "docTimeRel", "OVERLAP")
        links.append(new_link)

    ### MAKEINSTANCE ATTRIBUTES ###
    # contextualModality values
    if hasattr(event, "contextualModality") and event["contextualModality"]:
        if event["contextualModality"] == "HYPOTHETICAL-IF":
            new_event["instance"]["attrib"]["modality"] = "would" # approximate
        elif event["contextualModality"] == "HYPOTHETICAL-OTHER":
            new_event["instance"]["attrib"]["modality"] = "would" # approximate
        elif event["contextualModality"] == "HEDGED":
            new_event["instance"]["attrib"]["modality"] = "can"   # approximate
        elif event["contextualModality"] == "GENERIC":
            if new_event["attrib"].get("class") == "OCCURRENCE":
                new_event["attrib"]["class"] = "STATE"            # approximate
        # Value not converted: ACTUAL
        _addE3cComment(new_event["instance"]["attrib"], "contextualModality", event["contextualModality"])
    # permanence values
    if hasattr(event, "permanence") and event["permanence"]:
        if event["permanence"] == "PERMANENT":
            if new_event["attrib"].get("class") == "OCCURRENCE":
                new_event["attrib"]["class"] = "STATE"            # approximate
        # Value not converted: FINITE
        _addE3cComment(new_event["attrib"], "permanence", event["permanence"])
    # contextualAspect values
    if hasattr(event, "contextualAspect"):
        if event["contextualAspect"] == "NOVEL" or event["contextualAspect"] == "INTERMITTENT":
            _addE3cComment(new_event["instance"]["attrib"], "contextualAspect", event["contextualAspect"])
        # N/A is the implicit default
    # polarity values
    if hasattr(event, "polarity"):
        new_event["instance"]["attrib"]["polarity"] = event["polarity"]  # direct

    ### TLINKS ###
    if event.TLINK is not None and event.TLINK.elements is not None:
        for link in event.TLINK.elements:
            new_link = {
                "tag": "TLINK",
                "cas_id": event.xmiID,
                "cas_target_id": link.target.xmiID,
                "attrib": { "lid": "" }
            }
            # source and target attributes
            if link.type.name == "webanno.custom.TIMEX3TimexLinkLink":
                new_link["attrib"]["timeID"] = ""
            elif link.type.name == "webanno.custom.EVENTTLINKLink":
                new_link["attrib"]["eventInstanceID"] = ""
            else:
                continue
            if link.target.type.name == "webanno.custom.TIMEX3":
                new_link["attrib"]["relatedToTime"] = ""
            elif link.target.type.name == "webanno.custom.EVENT":
                new_link["attrib"]["relatedToEventInstance"] = ""
            else:
                continue
            # role values
            if link.role == "BEFORE":
                new_link["attrib"]["relType"] = "BEFORE"         # direct
            elif link.role == "OVERLAP":
                new_link["attrib"]["relType"] = "SIMULTANEOUS"   # approximate
                _addE3cComment(new_link["attrib"], "role", "OVERLAP")
            elif link.role == "CONTAINS":
                new_link["attrib"]["relType"] = "INCLUDES"       # equivalent
            elif link.role == "BEGINS-ON":
                new_link["attrib"]["relType"] = "BEGINS"         # equivalent
            elif link.role == "ENDS-ON":
                new_link["attrib"]["relType"] = "ENDS"           # equivalent
            elif link.role == "SIMULTANEOUS":
                new_link["attrib"]["relType"] = "SIMULTANEOUS"   # direct

            links.append(new_link)

    ### ALINKS ###
    if event.ALINK is not None and event.ALINK.elements is not None:
        for link in event.ALINK.elements:
            new_link = {
                "tag": "ALINK",
                "cas_id": event.xmiID,
                "cas_target_id": link.target.xmiID,
                "attrib": { "lid": "" }
            }
            # source and target attributes
            if link.type.name == "webanno.custom.TIMEX3TimexLinkLink":
                new_link["attrib"]["timeID"] = ""
            elif link.type.name == "webanno.custom.EVENTALINKLink":
                new_link["attrib"]["eventInstanceID"] = ""
            if link.target.type.name == "webanno.custom.TIMEX3":
                new_link["attrib"]["relatedToTime"] = ""
            elif link.target.type.name == "webanno.custom.EVENT":
                new_link["attrib"]["relatedToEventInstance"] = ""
            # role values
            new_link["attrib"]["relType"] = link.role     # direct
        
            links.append(new_link)

    return [new_event] + links

_DATE_PREFIX  = re.compile(r'^[0-9X]{1,4}(-[0-9X]{1,2}(-[0-9X]{1,2})?)?$')
_VALID_TIME_SUFFIX = re.compile(r'^(\d{2}(:\d{2}(:\d{2})?)?|MO|MI|AF|EV|NI|DT)$')

def _normalizeTimex3Value(timex3):
    # None or no_value -> unknown
    if not hasattr(timex3, "value") or timex3.value is None or timex3.value.lower() == "no_value":
        return "X"
    result = timex3.value
    # Duplicated unit suffix without P prefix: nDD -> P1D, nHH -> PTnH
    m = re.match(r'^\d+([YMWDHS])\1$', result)
    if m:
        unit = m.group(1)
        result = ("PT" if unit in ('H', 'S') else "P") + result[:-1]
    # Bare duration without P prefix: 4Y -> P4Y, 4H -> PT4H
    elif re.match(r'^\d+[YMWDHS]$', result):
        result = ("PT" if result[-1] in ('H', 'S') else "P") + result
    # Missing P prefix for T-duration: T6H -> PT6H
    elif re.match(r'^T[\d.]+[HMS]$', result):
        result = "P" + result
    # Underscores as date wildcards: __-__-__ -> XXXX-XX-XX
    if result.startswith('__'):
        result = 'XXXX' + result[2:]
    result = result.replace('__', 'XX')
    # Invalid T suffix on date: XXXX-XX-XXTXX -> XXXX-XX-XX
    t_pos = result.find("T")
    if t_pos > 0 and _DATE_PREFIX.match(result[:t_pos]) and not _VALID_TIME_SUFFIX.match(result[t_pos + 1:]):
        result = result[:t_pos]
    # Duration fixups
    if result.startswith("P"):
        # Range of durations -> midpoint: PT5-6H -> PT5.5H -> PT5H30M, P16-18W -> P17W
        while m := re.search(r'(\d+)-(\d+)([A-Z])', result):
            avg = (int(m.group(1)) + int(m.group(2))) / 2
            val = str(int(avg)) if avg.is_integer() else str(avg)
            result = result[:m.start()] + val + m.group(3) + result[m.end():]
        # Duplicated unit in duration: P1DD -> P1D, PT5HH -> PT5H
        result = re.sub(r'([YMWDHS])\1', r'\1', result)
        # Missing T separator before time: P6H -> PT6H
        if 'T' not in result and re.search(r'\d+[HS]', result):
            result = re.sub(r'(\d+[HS])', r'T\1', result, count=1)
        pre_decimal = result
        def _expand(m):
            decimal_value = float(m.group(1)); unit = m.group(2)
            integer_part = int(decimal_value); fractional_part = decimal_value - integer_part
            in_time_part = 'T' in pre_decimal[:m.start()]
            if unit == 'H':                    factor, next_unit = 60, 'M'
            elif unit == 'M' and in_time_part: factor, next_unit = 60, 'S'
            elif unit == 'M':                  factor, next_unit = 30, 'D'
            elif unit == 'D':                  factor, next_unit = 24, 'H'
            elif unit == 'Y':                  factor, next_unit = 12, 'M'
            elif unit == 'W':                  factor, next_unit = 7,  'D'
            else: return str(round(decimal_value)) + unit
            remainder = round(fractional_part * factor)
            if remainder >= factor: return f"{integer_part + 1}{unit}"
            if unit == 'W':
                return f"{integer_part * 7 + remainder}D"
            if unit == 'D' and remainder:
                return f"{integer_part}DT{remainder}H"
            return f"{integer_part}{unit}{remainder}{next_unit}" if remainder else f"{integer_part}{unit}"
        # Decimal component -> integer + remainder in next unit: P1.5M -> P1M15D
        result = re.sub(r'(\d+\.\d+)([A-Z])', _expand, result)
        # W mixed with D: P6W6D -> P48D (XSD requires W alone)
        result = re.sub(r'P(\d+)W(\d+)D', lambda m: f"P{int(m.group(1)) * 7 + int(m.group(2))}D", result)
        # Unknown duration without unit: PXX -> PXD
        if result == "PXX":
            result = "PXD"
    return result if result else "X"

def translateTimex3(timex3, cas_text, cas_tail):
    new_timex3 = {
        "tag": "TIMEX3",
        "cas_id": timex3.xmiID,
        "attrib": { "tid": "", "type": "DATE", "value": _normalizeTimex3Value(timex3) },
        "text": cas_text,
        "tail": cas_tail,
    }
    links = []
    # timex3Class values
    if hasattr(timex3, "timex3Class"):
        if timex3.timex3Class == "DATE":
            new_timex3["attrib"]["type"] = "DATE"              # direct
        elif timex3.timex3Class == "TIME":
            new_timex3["attrib"]["type"] = "TIME"              # direct
        elif timex3.timex3Class == "DURATION":
            new_timex3["attrib"]["type"] = "DURATION"          # direct
        elif timex3.timex3Class == "QUANTIFIER":
            new_timex3["attrib"]["type"] = "SET"               # approximate
            _addE3cComment(new_timex3["attrib"], "timex3Class", "QUANTIFIER")
        elif timex3.timex3Class == "SET":
            new_timex3["attrib"]["type"] = "SET"               # direct
        elif timex3.timex3Class == "PREPOSTEXP":
            new_timex3["attrib"]["type"] = "DATE"              # approximate
            _addE3cComment(new_timex3["attrib"], "timex3Class", "PREPOSTEXP")
    # value loss
    if hasattr(timex3, "value") and timex3.value is not None and timex3.value.lower() == "no_value":
        _addE3cComment(new_timex3["attrib"], "value", "NO_VALUE")
    # temporalFunction
    new_timex3["attrib"]["temporalFunction"] = "true"          # default
    if hasattr(timex3, "timex3Class"):
        if timex3.timex3Class == "DATE":
            if re.match(r'\d{3}[\dX]', new_timex3["attrib"]["value"]):
                new_timex3["attrib"]["temporalFunction"] = "false"  # year present: self-anchored
        elif timex3.timex3Class == "TIME":
            if re.match(r'\d{3}[\dX]', new_timex3["attrib"]["value"]):
                new_timex3["attrib"]["temporalFunction"] = "false"  # year present: self-anchored
        elif timex3.timex3Class == "DURATION":
            if "X" not in new_timex3["attrib"]["value"]:
                new_timex3["attrib"]["temporalFunction"] = "false"  # known quantity: self-contained
    # functionInDocument values
    if hasattr(timex3, "functionInDocument"):
        if timex3.functionInDocument == "DOCTIME":
            new_timex3["attrib"]["functionInDocument"] = "CREATION_TIME"  # equivalent
        elif timex3.functionInDocument == "SECTIONTIME":
            _addE3cComment(new_timex3["attrib"], "functionInDocument", "SECTIONTIME")
        # OTHER is the implicit TimeML default
    # links
    if timex3.timexLink is not None and timex3.timexLink.elements is not None:
        for link in timex3.timexLink.elements:
            new_link = {
                "tag": "TLINK",
                "cas_id": timex3.xmiID,
                "cas_target_id": link.target.xmiID,
                "attrib": { "lid": "" }
            }
            # source and target attributes
            if link.type.name == "webanno.custom.TIMEX3TimexLinkLink":
                new_link["attrib"]["timeID"] = ""
            elif link.type.name == "webanno.custom.EVENTTLINKLink":
                new_link["attrib"]["eventInstanceID"] = ""
            else:
                continue
            if link.target.type.name == "webanno.custom.TIMEX3":
                new_link["attrib"]["relatedToTime"] = ""
            elif link.target.type.name == "webanno.custom.EVENT":
                new_link["attrib"]["relatedToEventInstance"] = ""
            else:
                continue
            # role values
            if link.role == "BEFORE":
                new_link["attrib"]["relType"] = "BEFORE"         # direct
            elif link.role == "OVERLAP":
                new_link["attrib"]["relType"] = "SIMULTANEOUS"   # approximate
                _addE3cComment(new_link["attrib"], "role", "OVERLAP")
            elif link.role == "SIMULTANEOUS":
                new_link["attrib"]["relType"] = "SIMULTANEOUS"   # direct
            elif link.role == "CONTAINS":
                new_link["attrib"]["relType"] = "INCLUDES"       # equivalent
            elif link.role == "ENDS-ON":
                new_link["attrib"]["relType"] = "ENDS"           # equivalent
            elif link.role == "BEGINS-ON":
                new_link["attrib"]["relType"] = "BEGINS"         # equivalent

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
    # Move comments to the end of attributes for better readability:
    for element in tml_elements:
        if "comment" in element["attrib"]:
            element["attrib"]["comment"] = element["attrib"].pop("comment")
        if element["tag"] == "EVENT" and "comment" in element["instance"]["attrib"]:
            element["instance"]["attrib"]["comment"] = element["instance"]["attrib"].pop("comment")

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
    dct_generated = False
    for meta in cas_metadata:
        if hasattr(meta, "documentId"):
            etree.SubElement(root, "DOCID").text = meta.documentId
        if hasattr(meta, "docTime") and not dct_generated:
            try:
                dct_parsed = parser.parse(meta.docTime)
                etree.SubElement(root, "TIMEX3", attrib={"tid": "t0", "type": "DATE", "value": dct_parsed.isoformat(), "functionInDocument": "CREATION_TIME", "temporalFunction": "false"}).text = meta.docTime
            except (ParserError, ValueError):
                etree.SubElement(root, "TIMEX3", attrib={"tid": "t0", "type": "DATE", "value": "NO_VALUE", "functionInDocument": "CREATION_TIME", "temporalFunction": "false"}).text = meta.docTime
            dct_generated = True

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
    # 4. Construct TML XML with events, timex3s, and links
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

def convertFile(e3cFile: str, typesystemfile: str = 'E3C-Corpus\\TypeSystem.xml') -> list:
    with open(typesystemfile, 'rb') as f:
        typesystem = load_typesystem(f)

    with open(e3cFile, 'rb') as f:
        try:
            cas = load_cas_from_xmi(f, typesystem=typesystem)
        except etree.XMLSyntaxError as e:
            return [False, f"Malformed XMI file: {e}"]
        except Exception as e:
            return [False, f"Error loading XMI: {e}"]

    tml = generateTimeML(cas)
    output_path = e3cFile + ".tml"
    with open(output_path, 'w', encoding='utf-8') as out_f:
        out_f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        out_f.write(etree.tostring(tml, pretty_print=True, encoding="unicode"))

    validation = validator.validateFile(output_path, 'tml-xsd')
    if validation[0]:
        return [True, output_path]
    else:
        return [False] + validation[1:]

def convert(xmlPath: str, typesystemfile: str = 'E3C-Corpus\\TypeSystem.xml', report_file: str = "conversion_report.txt"):
    NUMBER_OF_LINES_TO_PRINT = 10

    def _reportResult(f, name, result):
        valid = result[0]
        lines = result[1:]
        message = f"{name}: {'converted' if valid else f'{len(lines)} errors'}\n"
        print(message)
        f.write(message)
        if not valid:
            print("\n".join([f"   - {chr(10).join(str(e).splitlines()[:NUMBER_OF_LINES_TO_PRINT])}" for e in lines]) + "\n")
            f.write("\n".join([f"   - {e}" for e in lines]) + "\n")

    if os.path.isfile(xmlPath):
        with open(report_file, "w", encoding="utf-8") as f:
            try:
                result = convertFile(xmlPath, typesystemfile)
            except Exception as e:
                result = [False, str(e)]
            _reportResult(f, os.path.basename(xmlPath), result)
    elif os.path.isdir(xmlPath):
        with open(report_file, "w", encoding="utf-8") as f:
            for file in os.listdir(xmlPath):
                filePath = os.path.join(xmlPath, file)
                if not os.path.isfile(filePath):
                    continue
                detected = detectFormat(filePath)
                if detected != FileFormat.E3C:
                    print(f"Skipping {file} (format: {detected.name})")
                    continue
                print(f"Converting {file}...")
                try:
                    result = convertFile(filePath, typesystemfile)
                except Exception as e:
                    result = [False, str(e)]
                _reportResult(f, file, result)
    else:
        print(f"Error: '{xmlPath}' is not a valid file or directory")
