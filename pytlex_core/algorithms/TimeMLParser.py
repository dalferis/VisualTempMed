# Written by: vfern124
# Last updated: asing118

# Using regular expressions to parse the TimeML text
import re

from pytlex_core.data.Instance import Instance
from pytlex_core.data.Event import Event
from pytlex_core.data.Signal import Signal
from pytlex_core.data.Link import Link
from pytlex_core.data.TimeX import TimeX


# Helper function for parsing
def __parse_phrase(to_parse) -> str:
    to_parse = '>' + to_parse + '<'
    parse_pattern = re.compile(r'>([^<]+)<')
    parse_matches = parse_pattern.finditer(to_parse)
    phrase = ''
    for match_parses in parse_matches:
        phrase += match_parses.group(1)
    return phrase


def parse_events(time_ml_text) -> list[Event]:
    """
    Searches a given text for possible Event objects
    :param time_ml_text: a str tagged with Time ML Events
    :return: a list of Event objects
    """
    event_pattern = re.compile(r'<EVENT([^>]+)>((?:(?!</EVENT)[\S\s])+)</EVENT>')
    event_matches = event_pattern.finditer(time_ml_text)

    events = []
    for match_event in event_matches:
        eid_pattern = re.compile(r'eid="e(\d+)"')
        eid = int(eid_pattern.findall(match_event.group(1))[0])

        e_class_pattern = re.compile(r'class="([^"]+)"')
        e_class = e_class_pattern.findall(match_event.group(1))[0]

        stem_pattern = re.compile(r'stem="([^"]+)"')
        stem_temp = stem_pattern.findall(match_event.group(1))
        stem = None
        if len(stem_temp) != 0:
            stem = stem_temp[0]
        else:
            stem = match_event.group(2)

        events += [Event(eid, e_class, stem)]

    return events


def parse_signals(time_ml_text) -> list[Signal]:
    """
    Searches a given text for possible Signal objects
    :param time_ml_text: a str tagged with Time ML Signals
    :return: a list of Signal objects
    """
    signal_pattern = re.compile(r'<SIGNAL sid="s(\d+)">((?:(?!</SIGNAL)[\S\s])+)</SIGNAL>')
    signal_matches = signal_pattern.finditer(time_ml_text)

    signals = []
    for signal in signal_matches:
        signals += [Signal(int(signal.group(1)), __parse_phrase(signal.group(2)))]

    return signals


def parse_instances(time_ml_text) -> list[Instance]:
    """
    Searches a given text for possible Instance objects
    :param time_ml_text: a str tagged with Time ML Instances
    :return: a list of Instance objects
    """
    event_list = parse_events(time_ml_text)
    signals = parse_signals(time_ml_text)

    instance_pattern = re.compile(r'<MAKEINSTANCE([^>]+)/>')
    instance_matches = instance_pattern.finditer(time_ml_text)

    instances = []
    for match_instance in instance_matches:
        eiid_pattern = re.compile(r'eiid="ei([^"]+)"')
        eiid = int(eiid_pattern.findall(match_instance.group(1))[0])

        eventID_pattern = re.compile(r'eventID="e([^"]+)"')
        eventID = int(eventID_pattern.findall(match_instance.group(1))[0])
        event = None
        for e in event_list:
            if e.eid == eventID:
                event = e
                break

        tense_pattern = re.compile(r'tense="([^"]+)"')
        tense = tense_pattern.findall(match_instance.group(1))[0]

        aspect_pattern = re.compile(r'aspect="([^"]+)"')
        aspect = aspect_pattern.findall(match_instance.group(1))[0]

        pol_pattern = re.compile(r'polarity="([^"]+)"')
        pol = pol_pattern.findall(match_instance.group(1))[0]

        signal_pattern = re.compile(r'signalID="s(\d+)"')
        signal_temp = signal_pattern.findall(match_instance.group(1))
        signal = None
        if len(signal_temp) != 0:
            signal_id = int(signal_temp[0])

            for s in signals:
                if s.signal_id == signal_id:
                    signal = s
                    break

        card_pattern = re.compile(r'cardinality="([^"]+)"')
        card_temp = card_pattern.findall(match_instance.group(1))
        cardinality = None
        if len(card_temp) != 0:
            cardinality = card_temp[0]

        pos_pattern = re.compile(r'pos="([^"]+)"')
        pos = pos_pattern.findall(match_instance.group(1))[0]

        mod_pattern = re.compile(r'modality="[^"]+"')
        mod_temp = mod_pattern.findall(match_instance.group(1))
        modality = None
        if len(mod_temp) != 0:
            modality = mod_temp[0]
        if signal is None:
            instances += [
                Instance(eiid, event.get_id_str(), event.event_class, tense, aspect, pos, pol, modality, "",
                         cardinality)]

        else:
            instances += [Instance(eiid, event.get_id_str(), event.event_class, tense, aspect, pos,
                                   pol, modality, signal.get_id_str(), cardinality)]

    return instances


def parse_timex(time_ml_text) -> list[TimeX]:
    """
    Searches a given text for possible Timex objects
    :param time_ml_text: a str tagged with Time ML Timexes
    :return: a list of Timex objects
    """
    timex_pattern = re.compile(r'<TIMEX3([^>]+)>((?:(?!</TIMEX3)[\S\s])+)</TIMEX3>')
    timex_matches = timex_pattern.finditer(time_ml_text)
    timexes = []
    for match_timex in timex_matches:
        phrase = __parse_phrase(match_timex.group(2))

        tid_pattern = re.compile(r'tid="t(\d+)"')
        tid = int(tid_pattern.findall(match_timex.group(1))[0])

        type_pattern = re.compile(r'type="([^"]+)"')
        type_temp = type_pattern.findall(match_timex.group(1))
        type = 'NONE'
        if len(type_temp):
            type = type_temp[0]

        value_pattern = re.compile(r'value="([^"]+)"')
        value = value_pattern.findall(match_timex.group(1))[0]

        mod_pattern = re.compile(r'mod="([^"]+)"')
        mod_temp = mod_pattern.findall(match_timex.group(1))
        mod = 'NONE'
        if len(mod_temp):
            mod = mod_temp[0]

        temporal_pattern = re.compile(r'temporalFunction="([^"]+)"')
        temporal = bool(temporal_pattern.findall(match_timex.group(1))[0])

        func_doc_pattern = re.compile(r'functionInDocument="([^"]+)"')
        func_doc_temp = func_doc_pattern.findall(match_timex.group(1))
        func_doc = 'NONE'
        if len(func_doc_temp):
            func_doc = func_doc_temp[0]

        anchor_pattern = re.compile(r'anchorTimeID="t(\d+)"')
        anchor_temp = anchor_pattern.findall(match_timex.group(1))
        anchor = None
        if len(anchor_temp):
            anchor = int(anchor_temp[0])

        quant_pattern = re.compile(r'quant="[^"]*"')
        quant_temp = quant_pattern.findall(match_timex.group(1))
        quant = None
        if len(quant_temp):
            quant = quant_temp[0]

        freq_pattern = re.compile(r'freq="([^"]+)"')
        freq_temp = freq_pattern.findall(match_timex.group(1))
        freq = None
        if len(freq_temp):
            freq = freq_temp[0]

        begin_point_pattern = re.compile(r'beginPoint="t([^"]+)"')
        begin_point_temp = begin_point_pattern.findall(match_timex.group(1))
        begin_point = None
        if len(begin_point_temp):
            begin_point = int(begin_point_temp[0])

        end_point_pattern = re.compile(r'endPoint="t([^"]+)"')
        end_point_temp = end_point_pattern.findall(match_timex.group(1))
        end_point = None
        if len(end_point_temp):
            end_point = int(end_point_temp[0])

        timexes += [TimeX(tid, value, temporal, phrase, type, mod, func_doc,
                          anchor, quant, freq, begin_point, end_point)]
    return timexes


def parse_links(time_ml_text) -> list[Link]:
    """
    Searches a given text for possible Link objects
    :param time_ml_text: a str tagged with Time ML Links
    :return: a list of Link objects
    """
    instances = parse_instances(time_ml_text)
    signals = parse_signals(time_ml_text)
    timexes = parse_timex(time_ml_text)

    link_pattern = re.compile(r'<([AST]LINK)([^>]+)/>')
    link_matches = link_pattern.finditer(time_ml_text)

    links = []
    for match_link in link_matches:
        tag = match_link.group(1)

        link_id_pattern = re.compile(r'lid="l([\d]+)"')
        link_id = int(link_id_pattern.findall(match_link.group(2))[0])

        rel_type_pattern = re.compile(r'relType="([^"]+)"')
        rel_type = rel_type_pattern.findall(match_link.group(2))[0]

        start_pattern = re.compile(r'timeID="t(\d+)"')
        start_temp = start_pattern.findall(match_link.group(2))
        start = None
        if len(start_temp) != 0:
            for t in timexes:
                if t.tID == int(start_temp[0]):
                    start = t
                    break
        else:
            start_pattern = re.compile(r'eventInstanceID="ei(\d+)"')
            start_temp = start_pattern.findall(match_link.group(2))
            if len(start_temp) != 0:
                for i in instances:
                    if i.event_instance_id == int(start_temp[0]):
                        start = i
                        break

        related_pattern = re.compile(r'relatedToTime="t(\d+)"')
        related_temp = related_pattern.findall(match_link.group(2))
        related = None
        if len(related_temp) != 0:
            for t in timexes:
                if t.tID == int(related_temp[0]):
                    related = t
                    break
        else:
            related_pattern = re.compile(r'(subordinatedEventInstance|relatedToEventInstance)="ei(\d+)"')
            related_temp = related_pattern.findall(match_link.group(2))
            if len(related_temp) != 0:
                for i in instances:
                    if i.event_instance_id == int(related_temp[0][1]):
                        related = i
                        break

        signal_pattern = re.compile(r'signalID="s(\d+)"')
        signal_temp = signal_pattern.findall(match_link.group(2))
        signal = None
        if len(signal_temp) != 0:
            for s in signals:
                if s.signal_id == int(signal_temp[0]):
                    signal = s
                    break

        origin_pattern = re.compile(r'origin="([^"]+)"')
        origin_temp = origin_pattern.findall(match_link.group(2))
        origin = None
        if len(origin_temp) != 0:
            origin = origin_temp[0]
        if signal is None:
            links += [
                Link(link_id, tag, rel_type, start.get_id_str(), related.get_id_str(), "", origin)]
        else:
            links += [Link(link_id, tag, rel_type, start.get_id_str(), related.get_id_str(), signal.get_id_str(), origin)]
    return links


def parse_raw_text(time_ml_text) -> str:
    # Catches '<s>...</s>' so that newline characters can be added in between each sentence.
    raw_text_pattern = re.compile(r'<s>((?:(?!</s>)[\S\s])+)</s>')
    raw_text_matches = raw_text_pattern.finditer(time_ml_text)
    phrase = ''
    for match_text in raw_text_matches:
        phrase += __parse_phrase(match_text.group(1)) + '\n'
    return phrase


def parse_metadata(time_ml_text) -> list[str]:
    # First find where the text begins
    text_match = re.compile(r'<TEXT>').finditer(time_ml_text)
    stop = 0
    for match in text_match:
        stop = int(match.span()[0])

    # Then collect any matches before the text, which correspond to the metadata
    meta_pattern = re.compile(r'<(\w+)>((?:(?!</\1>)[\S\s])+)(</\1>)')
    meta_matches = meta_pattern.finditer(time_ml_text[0: stop:])

    data = []
    for match_data in meta_matches:
        phrase = __parse_phrase(match_data.group(2))
        data += [[match_data.group(1), phrase]]

    return data


def parse(time_ml_text) -> (str, str, list[Link], list[TimeX], list[Instance]):
    """
    Searches a given text for TimeML Tags
    :param time_ml_text: a str annotated in TimeML
    :return: the metadata, raw text, and then a list for each category: links, timexes, instances, signals, and events
    """
    return parse_metadata(time_ml_text), parse_raw_text(time_ml_text), parse_links(time_ml_text), \
           parse_timex(time_ml_text) + parse_instances(time_ml_text), parse_signals(time_ml_text), parse_events(
        time_ml_text)


def parse_dict(time_ml_text) -> (str, str, list[Link], list[TimeX], list[Instance], list[Event], list[Signal]):
    return {
        'metadata': parse_metadata(time_ml_text), 'raw_text': parse_raw_text(time_ml_text),
        'links': parse_links(time_ml_text), 'timexes': parse_timex(time_ml_text),
        'instances': parse_instances(time_ml_text), 'events': parse_events(time_ml_text),
        'signals': parse_signals(time_ml_text)
    }


def read_file_data(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()


if __name__ == "__main__":
    data = read_file_data('../pytlex_data/TimeBankCorpus/example_data.tml')
    output = parse_dict(data)

    for key in output:
        print(key, end=': ')
        print(output[key])
