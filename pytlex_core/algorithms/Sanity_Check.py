"""
Main function is to implement the Sanity Check rules on the corpus.

Created by: asing118

Last Updated by: asing118
"""

import re
from collections import Counter

from pytlex_core.algorithms import TimeMLParser
from pytlex_core.data import Instance, Event, Graph

causative_verb_list = ["cause", "causing", "causes", "caused", "stem from", "lead to", "breed", "engender", "hatch",
                       "induce",
                       "occasion",
                       "produce", "bring about", "secure", "secured"]  # For SCO to check causative verbs in sentences


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
    num_cases = 0
    num_valid_rule = 0
    num_missing_identity = 0
    invalid_sentences = []
    valid_sentences = []
    data = TimeMLParser.read_file_data(time_ml_file)
    events_instances_list = TimeMLParser.parse_instances(data) # Grabbing all Instances
    links = TimeMLParser.parse_links(data) # Grabbing all links
    lp_sentences = re.findall((r'<LP>((?:(?!</LP>)[\S\s])+)</LP>'), data, re.DOTALL)  # Some files use LP instead of s
    sentences = re.findall("<s>(.*?)</s>", data, re.DOTALL)
    if len(lp_sentences) > 0: # If file contains <LP> sentences
        sentences = sentences + lp_sentences
    for sentence in sentences:
        events_list = TimeMLParser.parse_events(sentence)
        event_info = re.findall('<EVENT([^>]+)>(.*?)</EVENT>', sentence, re.DOTALL)  # Grabs the List of Events

        if len(events_list) >= 3:  # Making sure more than 3 events in a sentence
            event_words = [event_word[1] for event_word in event_info]  # Grabbing words of events
            causative_events = []

            for word in causative_verb_list:  # If there are phrase cases like "led to" or "lead to"
                if " " in word:
                    raw_sentence = re.sub("<[^<]+>", "", sentence)
                    if word in raw_sentence:
                        first_word = word.split()[0]
                        if first_word in event_words:
                            causative_events.append(first_word)
                            event_words.remove(first_word)

            single_causative_events = [verb for verb in event_words if
                                       verb in causative_verb_list]  # Grabbing causative events that are single word
            causative_events = causative_events + single_causative_events # Combining both
            if len(causative_events) > 0:
                for found_causative_event in causative_events:  # In case more than 1 causative event in a sentence
                    causative_event_text = None
                    num_cases += 1  # Add 1 to valid rule

                    for event in event_info:
                        if event[1] == found_causative_event:
                            causative_event_text = event[0]  # Grabbing event info

                    causative_event_eid = re.findall("eid=\"(.*?)\"", causative_event_text, re.DOTALL)  # Grabbing eid

                    causative_event: Event
                    for event in events_list:
                        if event.get_id_str() == causative_event_eid[0]:
                            causative_event = event  # Getting event object
                    events_list_ids = [event.get_id_str() for event in events_list]
                    causative_event_instance: Instance
                    instances: list = []
                    for instance in events_instances_list:
                        if instance.event in events_list_ids:
                            if instance.event == causative_event.get_id_str():
                                causative_event_instance = instance  # Finding causative event instance
                            else:
                                instances.append(instance)  # Grabbing instance object for events in sentence
                    found_identity = False
                    instances_list_ids = [instance.get_id_str() for instance in instances]
                    for link in links:
                        if link.rel_type == "IDENTITY":
                            if (causative_event_instance.get_id_str() == link.start_node) or (
                                    causative_event_instance.get_id_str() == link.related_to_node):
                                if (link.start_node in instances_list_ids) or (
                                        link.related_to_node in instances_list_ids): # Checks for IDENTITY link
                                    found_identity = True
                    if found_identity:  # If IDENTITY link is found
                        num_valid_rule += 1
                        valid_sentences.append(sentence)
                    else:  # If IDENTITY link is not found
                        num_missing_identity += 1
                        invalid_sentences.append(sentence)

    if num_cases < num_missing_identity:  # If an error occurs
        raise Exception("Incorrect! with file: ", time_ml_file, ", is somehow finding more violations than cases")

    if num_valid_rule > 0 or num_missing_identity > 0:  # Outputting
        print(time_ml_file)
        print("Number of e1-e2-e3 where e2 is a causative verb:\t", num_cases)
        if num_valid_rule > 0:
            print("Number of e1-e2-e3 where e2 is a causative verb with an IDENTITY link:\t", num_valid_rule)
            print("Sentences of e1-e2-e3 where e2 is a causative verb with an IDENTITY link:\t", valid_sentences)
        if num_missing_identity > 0:
            print("Number of e1-e2-e3 where there is no e1-IDENTITY-e2:\t", num_missing_identity)
            print("Sentences with e1-e2-e3 where there is no e1-IDENTITY-e2:\t", invalid_sentences)
        print("")
    return num_cases, num_valid_rule, num_missing_identity


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
            if link.start_node == event.get_id_str() or link.related_to_node == event.get_id_str():
                used_nodes.append(event)  # Checks if an event is used in any link
        for timex in timex_instances:
            if link.start_node == timex.get_id_str() or link.related_to_node == timex.get_id_str():
                used_nodes.append(timex)  # Checks if a timex is used in any link

    for event in event_instances:
        if event not in used_nodes:
            unused_nodes.append(event)  # Adds events not used to unused_nodes list
    for timex in timex_instances:
        if timex not in used_nodes:
            unused_nodes.append(timex)  # Adds timexes not used to unused_nodes list
    print("Orphaned Nodes:\t", unused_nodes)
    return unused_nodes


def node_to_node(filepath):
    """
    Represents the Node to Node rule from Sanity Check.

    Each possible pair of nodes cannot have more than 3 links between them.
    As such, this method checks that no pair of nodes violate that rule.
    """
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
    for link in links.values():
        if "eiid" in link.start_node and "eiid" in link.related_to_node:
            start_node_event = int(graph.nodes.get(link.start_node).event[1:])
            related_node_event = int(graph.nodes.get(link.related_to_node).event[1:])

            countLinks.append((link, (start_node_event, related_node_event)))
            counts[(start_node_event, related_node_event)] = \
                counts.get((start_node_event, related_node_event), 0) + 1
        if "t" in link.start_node and "t" in link.related_to_node:
            start_node_event = int(link.start_node[1:])
            related_node_event = int(link.related_to_node[1:])

            countLinks.append((link, (start_node_event, related_node_event)))
            counts[(start_node_event, related_node_event)] = \
                counts.get((start_node_event, related_node_event), 0) + 1
        if "eiid" in link.start_node and "t" in link.related_to_node:
            start_node_event = int(graph.nodes.get(link.start_node).event[1:])
            related_node_event = int(link.related_to_node[1:])

            countLinks.append((link, (start_node_event, related_node_event)))
            counts[(start_node_event, related_node_event)] = \
                counts.get((start_node_event, related_node_event), 0) + 1
        if "t" in link.start_node and "eiid" in link.related_to_node:
            start_node_event = int(link.start_node[1:])
            related_node_event = int(graph.nodes.get(link.related_to_node).event[1:])

            countLinks.append((link, (start_node_event, related_node_event)))
            counts[(start_node_event, related_node_event)] = \
                counts.get((start_node_event, related_node_event), 0) + 1
    # Now we need to determine which node pairs exceed the 3 links between them limit
    # Store these nodes's IDs in its own list
    criminal_ids = list()
    for ids, count in counts.items():
        if count > 2:
            criminal_ids.append(ids)
            # Point out which nodes these are and print out the links corresponding to that pair
            print("The nodes with IDs", ids, "have", count, "links between them. These links are:")
            for nodLink, nodePair in countLinks:
                if nodePair == ids:
                    print(nodLink)
    # If no nodes break the rule, stop here
    # Otherwise, now we need to find out which sentences these links belong to
    if len(criminal_ids) == 0:
        print("No nodes in this file break the node-to-node rule.")
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
        print("The sentences that include these links are:")
        for sentence in badSentences:
            print(sentence)
        return len(badSentences)


def perception_rule(filepath):
    """
    Represents the Perception Rule from Sanity Check.

    Perception events must always introduce either EVIDENTIAL or NEG_EVIDENTIAL link relation types.
    This method checks each perception event in the corpus to make sure they introduce said link.
    """
    # create the graph given the filepath
    graph = Graph.Graph(filepath=filepath)
    links = graph.links.values()
    nodes = graph.nodes.values()
    events = graph.events.values()
    perception_events = []
    perception_nodes = []
    violation_nodes = []
    valid_nodes = []
    for event in events:
        if event.event_class == 'PERCEPTION':  # Adds all perception events to a list
            perception_events.append(event)

    for event in perception_events:
        for node in nodes:
            if hasattr(node, "event") and event.get_id_str() == node.event:  # Gathers the event objects
                perception_nodes.append(node)
    for perception_node in perception_nodes:
        introduced_evidential_link = False
        for link in links:
            if link.link_tag == "SLINK":
                if link.start_node == perception_node.get_id_str():  # Checks for a link that contains the event
                    if link.rel_type == "EVIDENTIAL" or link.rel_type == "NEG_EVIDENTIAL":
                        introduced_evidential_link = True
        if introduced_evidential_link:  # if the Perception event does introduce a EVIDENTIAL/NEG_EVIDENTIAL link
            valid_nodes.append(perception_node)
        else:  # if the Perception event does not
            violation_nodes.append(perception_node)
    if len(valid_nodes) > 0:
        print("Perception Nodes that introduce EVIDENTIAL/NEG_EVIDENTIAL Links: ", valid_nodes)
    if len(violation_nodes) > 0:
        print("Perception Nodes that DO NOT introduce EVIDENTIAL/NEG_EVIDENTIAL Links: ", violation_nodes)

    return valid_nodes, violation_nodes


def repeating_links(filepath):
    """
    Represents the Repeating Links rule from Sanity Check.

    Checks for dupliate links in each file.
    """
    data = TimeMLParser.read_file_data(filepath)
    links = TimeMLParser.parse_links(data)  # Grabs Links
    duplicates = [link for link, counter in Counter(links).items() if counter > 1]  # Checks for multiple instances

    if len(duplicates) > 0:  # Prints out Duplicates if there are
        print("# of Duplicate Links: ", len(duplicates))
        print(duplicates)
    return duplicates


def conditional_slink_rule(filepath):
    """
    Represents the Conditional SLINK Rule from Sanity Check.

    A conditional conjunction can be defined by two cases:
        - … <EVENT> … if … <EVENT>
        - If … <EVENT> …, … <EVENT>

    If said case appears, there must be a CONDITIONAL SLINK
    between the two events in said sentence.

    The method checks every sentence in a file to see if the
    case appears before checking if there is a correct
    CONDITIONAL SLINK identified between the two events.
    """
    data = TimeMLParser.read_file_data(filepath)
    lp_sentences = re.findall((r'<LP>((?:(?!</LP>)[\S\s])+)</LP>'), data, re.DOTALL)
    sentences = re.findall("<s>(.*?)</s>", data, re.DOTALL)
    if len(lp_sentences) > 0:
        sentences = sentences + lp_sentences
    graph = Graph.Graph(filepath=filepath)
    links = graph.links.values()
    nodes = graph.nodes.values()
    if_sentences = []
    cases = {}
    found_cases = []
    valid_cases = []
    invalid_cases = []
    found_slinks = []

    for sentence in sentences:
        events_list = TimeMLParser.parse_events(sentence)
        if len(events_list) >= 2:  # Making sure there is atleast 2 events in the sentence
            if_clause_one = re.findall(
                '</EVENT>(?:(?!(\'if|\"if|>if<| if )|<EVENT).)*(\'if|\"if|>if<| if )(?:(?!(\'if|\"if|>if<| if )|<EVENT).)*<EVENT',
                sentence, re.DOTALL)  # Checking for first case + if there are capitals/quotation marks
            if_clause_two = re.findall(
                '(If | if |>if<|>If<|\"If|\'If|\'if|\"if)(?:(?!<EVENT|<EVENT).)*<EVENT(?:(?!<EVENT|<EVENT).)*<EVENT',
                sentence,
                re.DOTALL)  # Checking for the second case + if there are capitals/quotation marks

            if len(if_clause_one) > 0:
                if_sentences.append(sentence)
                cases[sentence] = [if_clause_one, 1]
            elif len(if_clause_two) > 0:
                if_sentences.append(sentence)
                cases[sentence] = [if_clause_two, 2]

    for case in cases:
        found_SLINK = False
        if cases[case][1] == 1:  # For the first conditional conjunction: … <EVENT> … if … <EVENT>
            text_for_split: str
            if type(cases[case][0][0]) is tuple:  # AP900815-0044.tml returns a tuple
                tuple_version = cases[case][0][0]
                for tuple_value in tuple_version:
                    if "if" in tuple_value:
                        text_for_split = tuple_value
            else:
                text_for_split = cases[case][0][0]
            split_sentence = case.split(text_for_split)  # Splits the sentence at the found if

            if type(cases[case][0][0]) is tuple:
                first_event_sentence = split_sentence[0] + '>'
                second_event_sentence = '<' + split_sentence[1]
            else:
                first_event_sentence = split_sentence[0] + '</EVENT>'
                second_event_sentence = '<EVENT' + split_sentence[1]

            first_events_list = TimeMLParser.parse_events(first_event_sentence)[-1:]
            second_events_list = TimeMLParser.parse_events(second_event_sentence)
            first_event = first_events_list[0]  # Grabs the last event from the first half of the sentence
            second_event = second_events_list[0]  # Grabs the first event from the second half of the sentence
            first_instance: Instance
            second_instance: Instance
            for instance in nodes:  # Finds their instance objects
                if "e" in instance.get_id_str():
                    if instance.event == first_event.get_id_str():
                        first_instance = instance
                    if instance.event == second_event.get_id_str():
                        second_instance = instance
            slinks = [link for link in links if "SLINK" in link.link_tag and "CONDITIONAL" in link.rel_type]
            for link in slinks:  # Checks if there is a CONDITIONAL SLINK between the two event instances
                if link.start_node == first_instance.get_id_str():
                    if link.related_to_node == second_instance.get_id_str():
                        found_SLINK = True
                        found_slinks.append(link)
                elif link.start_node == second_instance.get_id_str():
                    if link.related_to_node == first_instance.get_id_str():
                        found_SLINK = True
                        found_slinks.append(link)

        if cases[case][1] == 2:  # For the second conditional conjunction: If … <EVENT> …, … <EVENT>
            events = TimeMLParser.parse_events(case)
            first_event = events[0]  # Grabs first event of sentence
            second_event = events[1]  # Grabs second event of sentence
            first_instance: Instance
            second_instance: Instance
            for instance in nodes:  # Grabs their event objects
                if "e" in instance.get_id_str():
                    if instance.event == first_event.get_id_str():
                        first_instance = instance
                    if instance.event == second_event.get_id_str():
                        second_instance = instance
            slinks = [link for link in links if "SLINK" in link.link_tag and "CONDITIONAL" in link.rel_type]
            for link in slinks:  # Checks for a CONDITIONAL SLINK between the two event instances
                if link.start_node == first_instance.get_id_str():
                    if link.related_to_node == second_instance.get_id_str():
                        found_SLINK = True
                        found_slinks.append(link)
                elif link.start_node == second_instance.get_id_str():
                    if link.related_to_node == first_instance.get_id_str():
                        found_SLINK = True
                        found_slinks.append(link)

        if found_SLINK:  # If a CONDITIONAL SLINK is found
            found_cases.append(case)
            valid_cases.append(case)
        else:  # If a CONDITIONAL SLINK is not found
            found_cases.append(case)
            invalid_cases.append(case)

    if len(found_cases) > 0:  # Outputting
        print("\n File: ", filepath)
        print("# of if clauses found: ", len(found_cases))
        if len(valid_cases) > 0:
            print("# of valid if clauses w/ conditional SLINKs: ", len(valid_cases))
            print("Links: ", found_slinks)
            print(valid_cases)
        if len(invalid_cases) > 0:
            print("# of if clauses MISSING a conditional SLINK: ", len(invalid_cases))
            print(invalid_cases)
    return found_cases, valid_cases, invalid_cases


def ALINK_rule(filepath):
    """
    Represents the ALINK - Link Incorrect Rule from Sanity Check.

    An ALINK link can be represented as a link with an ASPECTUAL
    event for a start node and an argument event as the related
    node.
    """
    # parse the file for any identifiable ALINKS
    data = TimeMLParser.read_file_data(filepath)
    events = TimeMLParser.parse_events(data)
    links = TimeMLParser.parse_links(data)
    valid_ALINKS = []
    for link in links:
        if link.link_tag == 'ALINK':  # Grabs all ALINK start nodes
            valid_ALINKS.append(link.start_node)

    # Grab all instances
    instances = TimeMLParser.parse_instances(data)
    error_list = []

    # Check instances for not 'ASPECTUAL'
    for instance in instances:
        for alink in valid_ALINKS:
            if instance.get_id_str() == alink:
                alink_event = None
                for event in events:
                    if instance.event == event.get_id_str():
                        alink_event = event
                if alink_event.event_class != 'ASPECTUAL':
                    error_list.append(alink_event)

    sentence_result = []

    # Find all tags related to the instances
    s_tags = re.findall("<s>(.*?)</s>", data, re.DOTALL)
    LP_tags = re.findall("<LP>(.*?)</LP>", data, re.DOTALL)
    LEADPARA_tags = re.findall("<LEADPARA>(.*?)</LEADPARA>", data, re.DOTALL)

    # Join the lists
    tags = s_tags + LP_tags + LEADPARA_tags
    for i in range(len(error_list)):  # Grabbing sentence if there is an incorrect ALINK
        sample = error_list[i].eid
        value = "e" + str(sample)
        for field in tags:
            if value in field:
                sentence_result.append(field)

    print("Number of ALINKS that violate rule: %d" % (len(error_list)))  # Outputting
    print("List of ALINKS: ")
    for i in range(len(error_list)):
        print("%d)" % (i + 1), error_list[i])
    print(sentence_result)
    return len(valid_ALINKS), len(error_list)


def redundant_self_loops(filepath):
    """
    Represents the Redundant Self Loops Rule from Sanity Check.

    A self loop is when there is a link that has an event as both
    its start node and related node. There are only two valid cases
    if there is a link like that:
        - A SIMULTANEOUS link
        - An IDENTITY link
    Otherwise this is a redundant self loop.

    As such, this method checks for all redundant self loops in a
    file.
    """
    graph = Graph.Graph(filepath=filepath)
    links = graph.links.values()
    self_loops = []

    for link in links:
        if link.start_node == link.related_to_node and (
                link.rel_type != "SIMULTANEOUS") and (link.rel_type != "IDENTITY"):  # Checking for invalid self loops
            self_loops.append(link)
    if self_loops is not None:  # Outputting
        print(self_loops)
    return self_loops
