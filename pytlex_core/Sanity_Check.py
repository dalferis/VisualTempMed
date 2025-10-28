"""
Main function is to implement the Sanity Check rules on the corpus.

Created by: asing118

Last Updated by: asing118
"""

from pytlex_core import Graph
from pytlex_core import Event
from pytlex_core import Link
from pytlex_core import TimeX
from pytlex_core import Instance
from pytlex_core import TimeMLParser
import re

causative_verb_list = ["cause", "stem from", "lead to", "breed", "engender", "hatch", "induce", "occasion",
                       "produce", "bring about", "produce", "secure"]


def sco_identity_rule(time_ml_file):
    """
    Represents the Subject, Causative, Object - Identity Rule from Sanity Check.

    Looks for if an event is introduced through a causative relation event in the order of e1-e2-e3 where e2 is the
    causative event. Utilizes a list of causative verbs to check if the event is valid.

    From there, it checks if an IDENTITY link has been identified between the events in the sentence.

    It outputs how many sentences contain a sequence of e1-e2-e3 with a causative verb. It then checks if there
    is a missing IDENTITY link from e1 to e2. Then finally returns the sentence if there is no identity link between
    e1 and e3.
    """
    num_valid_rule = 0
    num_missing_identity = 0
    invalid_sentences = []
    data = TimeMLParser.read_file_data(time_ml_file)
    events_instances_list = TimeMLParser.parse_instances(data)
    sentences = re.findall("<s>(.*?)</s>", data, re.DOTALL)
    for sentence in sentences:
        events_list = TimeMLParser.parse_events(sentence)
        event_words = re.findall('<EVENT([^>]+)>(.*?)</EVENT>', sentence, re.DOTALL)
        causative_events = []
        causative_event = Event
        causative_event_instance = Instance
        if len(events_list) >= 3:
            for verb in causative_verb_list:
                for word in event_words:
                    if verb in word[1]:
                        causative_events.append(word)

            if causative_events:  # If a causative event is found
                num_valid_rule += 1
                causative_event_info = causative_events[0][0]
                causative_event_eid = re.findall("eid=\"e(.*?)\"", causative_event_info, re.DOTALL)
                for event in events_list:
                    if event.eid == int(causative_event_eid[0]):
                        causative_event = event  # Gets Causative Event
                final_instances = []
                for instance in events_instances_list:  # Gathers the list of Instances of Events for checking links
                    for event in events_list:
                        if instance.event.eid == event.eid:
                            final_instances.append(instance)
                        if causative_event.eid == instance.event.eid:
                            causative_event_instance = instance

                links = TimeMLParser.parse_links(data)
                for instance in final_instances:
                    for link in links:
                        if link.start_node == instance and link.related_to_node == causative_event_instance:
                            if link.rel_type != "IDENTITY":  # Checks if there is an IDENTITY link from e1 to e2
                                num_missing_identity += 1
                        for secondary_instance in final_instances:
                            if link.start_node == instance and link.related_to_node == secondary_instance and \
                                    link.related_to_node is not causative_event_instance:
                                if link.rel_type != "IDENTITY":  # Checks if there is any e1-e3 IDENTITY links
                                    already_in = False
                                    for invalid_sentence in invalid_sentences:
                                        if sentence == invalid_sentence:
                                            already_in = True  # Makes sure sentence isn't entered multiple times
                                    if not already_in:
                                        invalid_sentences.append(sentence)

    # print("Number of e1-e2-e3 where e2 is a causative verb:\t", num_valid_rule)
    # print("Number of e1-e2-e3 where there is no e1-IDENTITY-e2:\t", num_missing_identity)
    # print("Sentences with e1-e2-e3 where there is no e1-IDENTITY-e3:\t", invalid_sentences)
    return num_valid_rule, num_missing_identity


def orphaned_node_rule(filepath):
    """
    Represents the Orphaned Node rule from Sanity Check.

    An Orphaned Node is a node with no ingoing or outgoing links.

    Parses the TimeML file for it's events, TIMEX's, and links.
    From there, it checks if every event and TIMEX has been used in a link.
    If not, it gets added to a list and the list is returned as the output.
    """
    data = TimeMLParser.read_file_data(filepath)
    links = TimeMLParser.parse_links(data)
    event_instances = TimeMLParser.parse_instances(data)
    timex_instances = TimeMLParser.parse_timex(data)
    used_nodes = []
    unused_nodes = []
    for link in links:
        for event in event_instances:
            if link.start_node == event or link.related_to_node == event:
                used_nodes.append(event)
        for timex in timex_instances:
            if link.start_node == timex or link.related_to_node == timex:
                used_nodes.append(timex)
    for event in event_instances:
        if event not in used_nodes:
            unused_nodes.append(event)
    for timex in timex_instances:
        if timex not in used_nodes:
            unused_nodes.append(timex)
    # print("Orphaned Nodes:\t", unused_nodes)
    return unused_nodes


# Node-to-Node Rule
def node_to_node(filepath):
    # Create graph for a .tml file using the given filepath
    graph = Graph.Graph(filepath=filepath)
    # Get the links and file content from it
    links = graph.links
    time_ml_data = graph.time_ml_data

    # Use a dictionary to keep track of many times each combination of nodes appear across all links
    counts = dict()
    # Also store every link and its respective node IDs in its own list
    countLinks = list()
    # Go throughout every link and count node pairs
    # If the node is of Instance type, get the eID
    # If of TimeX type, get the tID instead
    for link in links:
        if isinstance(link.start_node, Instance.Instance) and isinstance(link.related_to_node, Instance.Instance):
            countLinks.append((link, (link.start_node.event.eid, link.related_to_node.event.eid)))
            counts[(link.start_node.event.eid, link.related_to_node.event.eid)] = \
                counts.get((link.start_node.event.eid, link.related_to_node.event.eid), 0) + 1
        if isinstance(link.start_node, TimeX.TimeX) and isinstance(link.related_to_node, TimeX.TimeX):
            countLinks.append((link, (link.start_node.tID, link.related_to_node.tID)))
            counts[(link.start_node.tID, link.related_to_node.tID)] = \
                counts.get((link.start_node.tID, link.related_to_node.tID), 0) + 1
        if isinstance(link.start_node, Instance.Instance) and isinstance(link.related_to_node, TimeX.TimeX):
            countLinks.append((link, (link.start_node.event.eid, link.related_to_node.tID)))
            counts[(link.start_node.event.eid, link.related_to_node.tID)] = \
                counts.get((link.start_node.event.eid, link.related_to_node.tID), 0) + 1
        if isinstance(link.start_node, TimeX.TimeX) and isinstance(link.related_to_node, Instance.Instance):
            countLinks.append((link, (link.start_node.tID, link.related_to_node.event.eid)))
            counts[(link.start_node.tID, link.related_to_node.event.eid)] = \
                counts.get((link.start_node.tID, link.related_to_node.event.eid), 0) + 1
    # Now we need to determine which node pairs exceed the 3 links between them limit
    # Store these nodes's IDs in its own list
    criminal_ids = list()
    for ids, count in counts.items():
        if count > 2:
            criminal_ids.append(ids)
            # Point out which nodes these are and print out the links corresponding to that pair
            # print("The nodes with IDs", ids, "have", count, "links between them. These links are:")
            # for nodLink, nodePair in countLinks:
            #     if nodePair == ids:
            #         # print(nodLink)

    # If no nodes break the rule, stop here
    # Otherwise, now we need to find out which sentences these links belong to
    if len(criminal_ids) == 0:
        # print("No nodes in this file break the node-to-node rule.")
        return 0
    else:
        # For this we need to look at the formatted NON-RAW text given in the .tml file
        # We only care about the text enclosed in <LP>...</LP> and <s>...</s>
        raw_text_matches1 = re.finditer((r'<LP>((?:(?!</LP>)[\S\s])+)</LP>'), time_ml_data)
        raw_text_matches2 = re.finditer((r'<s>((?:(?!</s>)[\S\s])+)</s>'), time_ml_data)
        # We can look at every sentence separately using the method .group(0)
        # Store them one by one in a list of sentences
        textSentences = list()
        for match_text in raw_text_matches1:
            textSentences.append(match_text.group(0))
        for match_text in raw_text_matches2:
            textSentences.append(match_text.group(0))

        # Finally, find the sentences that include the ID pairs included in criminal_ids
        # As in, the IDs of the node pairs that break the node-to-node rule
        badSentences = list()
        # These IDs will be preceded by "eid=e" or "tid=t" in the text, so check for that on
        # each sentence in order to avoid counting numbers given in the raw text itself
        for sentence in textSentences:
            for (id1, id2) in criminal_ids:
                if (("".join(["eid=\"e", str(id1), "\""]) in sentence) or (
                        "".join(["tid=\"t", str(id1), "\""]) in sentence)) \
                        and (("".join(["eid=\"e", str(id2), "\""]) in sentence) or (
                        "".join(["tid=\"t", str(id2), "\""]) in sentence)) \
                        and (sentence not in badSentences):
                    badSentences.append(sentence)
        # Finally, print these sentences
        # Formatted form is preferred so the user can locate the IDs in the text
        # print("The sentences that include these links are:")
        # for sentence in badSentences:
        #     print(sentence)
        return len(badSentences)


# The perception rule says that PERCEPTION events will always introduce EVIDENTIAL or NEG_EVIDENTIAL relation types.
def perception_rule(filepath):
    # create the graph given the filepath
    graph = Graph.Graph(filepath=filepath)
    links = graph.links
    nodes = graph.nodes
    perception_nodes = []
    correct_nodes = 0
    incorrect_nodes = 0
    found_nodes = []
    found_incorrect = []
    for node in nodes:
        if type(node) is TimeX.TimeX:
            continue
        else:
            if node.event.event_class == 'PERCEPTION':
                perception_nodes.append(node)

    for link in links:
        for p_node in perception_nodes:
            if link.start_node == p_node and link.link_tag == "SLINK":
                if link.rel_type == 'EVIDENTIAL' or link.rel_type == 'NEG_EVIDENTIAL':
                    if p_node not in found_nodes:
                        correct_nodes += 1
                        # print(p_node.to_json())
                        found_nodes.append(p_node)
                else:
                    if p_node not in found_incorrect:
                        incorrect_nodes += 1
                        found_incorrect.append(p_node)

    # #save the SLINKS in the raw file
    # slinks = re.findall(r"<SLINK [^>]*>", graph.time_ml_data)
    #
    # perception_eids = []
    # failed_perception = []  # list containing failed SLINKS
    #
    # # find all events that are PERCEPTION events
    # for l in links:
    #     if isinstance(l.start_node, Instance.Instance):
    #         if l.start_node.event.event_class == 'PERCEPTION':
    #             # append ei to the event instance for easier checking later on
    #             perception_eids.append('ei' + str(l.start_node.event_instance_id))
    #
    # # find PERCEPTION events that are not of type EVIDENTIAL or NEG_EVIDENTIAL
    # for e in perception_eids:
    #     for s in slinks:
    #         # strip everything from the SLINK but the eID and relType
    #         if re.search(r"subordinatedEventInstance=\"(.*?)\"", s).group(1) == e:
    #             if re.search(r"relType=\"(.*?)\"", s).group(1) != ('EVIDENTIAL' or 'NEG_EVIDENTIAL'):
    #                 failed_perception.append(s)
    #
    # print(f'Checking file {filepath} for incorrect PERCEPTION events...')
    # print(f'{len(perception_eids)} PERCEPTION events found')
    # print(f'{len(failed_perception)} Incorrect PERCEPTION events found')
    # if len(failed_perception) != 0:
    #     print('Incorrect SLINKS')
    #     for p in failed_perception:
    #         print(f'{p}')
    return len(perception_nodes), incorrect_nodes


# Find any repeating links in a given file and print them out
def repeating_links(filepath):
    # Get graph from a given .tml file
    graph = Graph.Graph(filepath=filepath)
    # Get the links and file content from it
    links = graph.links

    # Use a dictionary to count each combination of rel_type and IDs
    # If the node is of Instance type, get the eID
    # If of TimeX type, get the tID instead
    counts = dict()
    # Also store every link and its respective IDs + rel_type in its own list
    countLinks = list()
    for link in links:
        if isinstance(link.start_node, Instance.Instance) and isinstance(link.related_to_node, Instance.Instance):
            countLinks.append((link, (link.start_node.event.eid, link.related_to_node.event.eid, link.rel_type)))
            counts[(link.start_node.event.eid, link.related_to_node.event.eid, link.rel_type)] = \
                counts.get((link.start_node.event.eid, link.related_to_node.event.eid, link.rel_type), 0) + 1
        if isinstance(link.start_node, TimeX.TimeX) and isinstance(link.related_to_node, TimeX.TimeX):
            countLinks.append((link, (link.start_node.tID, link.related_to_node.tID, link.rel_type)))
            counts[(link.start_node.tID, link.related_to_node.tID, link.rel_type)] = \
                counts.get((link.start_node.tID, link.related_to_node.tID, link.rel_type), 0) + 1
        if isinstance(link.start_node, Instance.Instance) and isinstance(link.related_to_node, TimeX.TimeX):
            countLinks.append((link, (link.start_node.event.eid, link.related_to_node.tID, link.rel_type)))
            counts[(link.start_node.event.eid, link.related_to_node.tID, link.rel_type)] = \
                counts.get((link.start_node.event.eid, link.related_to_node.tID, link.rel_type), 0) + 1
        if isinstance(link.start_node, TimeX.TimeX) and isinstance(link.related_to_node, Instance.Instance):
            countLinks.append((link, (link.start_node.tID, link.related_to_node.event.eid, link.rel_type)))
            counts[(link.start_node.tID, link.related_to_node.event.eid, link.rel_type)] = \
                counts.get((link.start_node.tID, link.related_to_node.event.eid, link.rel_type), 0) + 1
    # Now we need to pick out which links happen more than once
    # Store these links in their own list
    criminal_links = list()
    for rlink, count in counts.items():
        if count > 1:
            for link, attributes in countLinks:
                if (attributes == rlink) and (link not in criminal_links):
                    criminal_links.append(link)
    # Finally, point out which link these are and print them out
    # Otherwise, if no links repeat, stop here
    # if len(criminal_links) == 0:
    #     print("No links in this file repeat.")
    # else:
    #     print("The following links are repeating links:")
    #     for link in criminal_links:
    #         print(link)


# The Conditional SLINK rule states that conditional conjunctions will always receive CONDITIONAL
# as stated on the Annotation guide (pg 54).
def conditional_slink_rule(filepath):
    graph = Graph.Graph(filepath=filepath)
    links = graph.links

    # save all sentences in the timebank
    lp_sentences = re.finditer((r'<LP>((?:(?!</LP>)[\S\s])+)</LP>'), graph.time_ml_data)
    sentences = re.finditer((r'<s>((?:(?!</s>)[\S\s])+)</s>'), graph.time_ml_data)

    # this list will be used to store all sentences that have "if" in them
    if_sentences = []

    # find conditional links
    conditional_links = []
    for l in links:
        if l.rel_type == 'CONDITIONAL':
            conditional_links.append(l)

    # find the sentences that have If or if in them and save them
    # make sure that the "if" clauses are correct
    # the definition is the following
    # <EVENT> ... </EVENT>... if ... <EVENT> ... </EVENT>
    # if ... <EVENT> ... </EVENT> ... , ... <EVENT> ... </EVENT>
    # there is a minimum of 4 counts of EVENT tags, so we will keep track of that count
    for lp in lp_sentences:
        if re.search(r'\bif|If\b', lp.group(0)) is not None:
            if_sentences.append(lp.group(0))
    for s in sentences:
        if re.search(r'\bif|If\b', s.group(0)) is not None:
            if_sentences.append(s.group(0))

    # here we save all sentences that have "if" in them, but no CONDITIONAL link
    if_sentences_no_conditional = []
    for s in if_sentences:
        if re.search(r'\bCONDITIONAL\b', s) is None:
            if_sentences_no_conditional.append(s)

    # this link will be used to store sentences that have CONDITIONAL links
    # but no if signals in them
    # have to search both <LP> and <s> tags
    conditional_sentences_no_if = []
    for c in conditional_links:
        for lp in lp_sentences:
            if re.search(r"eid=\"e(.*?)\"", lp.group(0)) == str(c.related_to_node.event_instance_id):
                if re.search(r'\bif|If\b', lp.group(0)) is None:
                    conditional_sentences_no_if.append(lp.group(0))
        for sen in sentences:
            if re.search(r"eid=\"e(.*?)\"", sen.group(0)) == str(c.related_to_node.event_instance_id):
                if re.search(r'\bif|If\b', sen.group(0)) is None:
                    conditional_sentences_no_if.append(sen.group(0))

    # # just format the output for prettier viewing :)
    # print(f'Checking file {filepath} for conditional SLINK rule conformance...')
    # print(f'{len(if_sentences)} "if" clauses found')
    # print(f'{len(conditional_links)} CONDITIONAL links found')
    # if len(if_sentences_no_conditional) != 0:
    #     print(f'{len(if_sentences_no_conditional)} Sentences with "if" clauses but no CONDITIONAL link\n')
    #     for s in if_sentences_no_conditional:
    #         print(f'{s}\n')
    # else:
    #     print('Found 0 sentences with "if" clauses but no CONDITIONAL link')
    #
    # if len(conditional_sentences_no_if) != 0:
    #     print(f'{len(conditional_sentences_no_if)} Sentences with CONDITIONAL link but no "if" clause\n')
    #     for cs in conditional_sentences_no_if:
    #         print(f'{cs}\n')
    # else:
    #     print('Found 0 sentences with CONDITIONAL link but no "if" clause')
    return len(if_sentences), len(if_sentences) - len(conditional_links)


def ALINK_rule(filepath):
    # parse the file for any identifiable ALINKS
    data = TimeMLParser.read_file_data(filepath)
    links = TimeMLParser.parse_links(data)
    valid_ALINKS = []
    for link in links:
        if link.link_tag == 'ALINK':
            valid_ALINKS.append(link.start_node)

    # Grab all instances
    instances = TimeMLParser.parse_instances(data)
    error_list = []

    # Check instances for not 'ASPECTUAL'
    for instance in instances:
        for alink in valid_ALINKS:
            if instance.event_instance_id == alink.event_instance_id:
                if alink.event.event_class != 'ASPECTUAL':
                    error_list.append(alink)

    sentence_result = []

    # Find all tags related to the instances
    s_tags = re.findall("<s>(.*?)</s>", data, re.DOTALL)
    LP_tags = re.findall("<LP>(.*?)</LP>", data, re.DOTALL)
    LEADPARA_tags = re.findall("<LEADPARA>(.*?)</LEADPARA>", data, re.DOTALL)

    # Join the lists
    tags = s_tags + LP_tags + LEADPARA_tags
    for i in range(len(error_list)):
        sample = error_list[i].event.eid
        value = "e" + str(sample)
        for field in tags:
            if value in field:
                sentence_result.append(field)

    # print("Number of ALINKS that violate rule: %d" % (len(error_list)))
    # print("List of ALINKS: ")
    # for i in range(len(error_list)):
    #     print("%d)" % (i + 1), error_list[i])
    # print(sentence_result)
    return len(valid_ALINKS), len(error_list)


def redundant_self_loops(filepath):
    graph = Graph.Graph(filepath=filepath)
    links = graph.links
    self_loops = []

    for link in links:
        if link.start_node == link.related_to_node and (
                link.rel_type == "SIMULTANEOUS" or link.rel_type == "IDENTITY"):
            self_loops.append(link)
    return self_loops
