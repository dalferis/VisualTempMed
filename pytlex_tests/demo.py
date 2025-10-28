from pytlex_core.data import Graph
from timeit import default_timer as timer


def cls(): print("\n"*80)


# break on every cls() and line 18
if __name__ == '__main__':
    cls()
    print(" __          __  _                               _            _______ _      ________   __\n\
 \\ \\        / / | |                             | |          |__   __| |    |  ____\\ \\ / /\n\
  \\ \\  /\\  / /__| | ___ ___  _ __ ___   ___     | |_ ___        | |  | |    | |__   \\ V / \n\
   \\ \\/  \\/ / _ \\ |/ __/ _ \\| '_ ` _ \\ / _ \\    | __/ _ \\       | |  | |    |  __|   > < \n\
    \\  /\\  /  __/ | (_| (_) | | | | | |  __/    | || (_) |      | |  | |____| |____ / . \\\n\
     \\/  \\/ \\___|_|\\___\\___/|_| |_| |_|\\___|     \\__\\___/       |_|  |______|______/_/ \\_\\")
    print("\nLet's build a couple graphs:")
    start = timer()

    wsj_0006 = Graph.Graph(filepath=r"../pytlex_data/TimeBankCorpus/wsj_0006.tml")
    wsj_0026 = Graph.Graph(filepath=r"../pytlex_data/TimeBankCorpus/wsj_0026.tml")

    print("wsj_0006 = {}".format(wsj_0006))
    print("wsj_0026 = {}".format(wsj_0026))
    print("\nNote: all processing was done there, including: Parsing, Partitioning, Inconsistency Detection, Indeterminacy Detection, and Timeline Extraction")
    end = timer()
    print("Elapsed time: {}s".format(round(end-start, 2)))

    cls()
    print("But, let's break down every step...")
    cls()
    print("Starting with exploring how we parse wsj_0006...")
    cls()
    print("Here's the TimeML annotated text:\n\n")
    print("<TEXT>\n<s><ENAMEX TYPE='ORGANIZATION'>Pacific First Financial Corp.</ENAMEX> <EVENT eid='e1' class='REPORTING'>said</EVENT> shareholders <EVENT eid='e2' class='OCCURRENCE'>approved</EVENT>"
          " its <EVENT eid='e8' class='OCCURRENCE'>acquisition</EVENT> by <ENAMEX TYPE='ORGANIZATION'>Royal Trustco Ltd.</ENAMEX> of <ENAMEX TYPE='LOCATION'>Toronto</ENAMEX> for <NUMEX TYPE='MONEY'>$27</NUMEX>"
          " a share, or <NUMEX TYPE='MONEY'>$212 million</NUMEX>.</s><s>The thrift holding company <EVENT eid='e4' class='REPORTING'>said</EVENT> it <EVENT eid='e5' class='I_STATE'>expects</EVENT>  to "
          "<EVENT eid='e6' class='OCCURRENCE'>obtain</EVENT> regulatory <EVENT eid='e19' class='OCCURRENCE'>approval</EVENT> and <EVENT eid='e7' class='ASPECTUAL'>complete</EVENT> the <EVENT eid='e20' "
          "class='OCCURRENCE'>transaction</EVENT> <SIGNAL sid='s12'>by</SIGNAL> <TIMEX3 tid='t10' type='DATE' value='1989-12-31' temporalFunction='true' functionInDocument='NONE' anchorTimeID='t9'>year-end</TIMEX3>"
          ".</s> \n</TEXT>")
    cls()
    print("\n\nWhich gets broken into Events, Time Expressions (Timex), and Signals...\n")
    print("\
        <EVENT eid='e1' class='REPORTING'>said</EVENT> \n\
        <EVENT eid='e2' class='OCCURRENCE'>approved</EVENT> \n\
        <EVENT eid='e8' class='OCCURRENCE'>acquisition</EVENT> \n\
        <EVENT eid='e4' class='REPORTING'>said</EVENT> \n\
        <EVENT eid='e5' class='I_STATE'>expects</EVENT> \n\
        <EVENT eid='e6' class='OCCURRENCE'>obtain</EVENT> \n\
        <EVENT eid='e19' class='OCCURRENCE'>approval</EVENT> \n\
        <EVENT eid='e7' class='ASPECTUAL'>complete</EVENT> \n\
        <EVENT eid='e20' class='OCCURRENCE'>transaction</EVENT> \n\
        <SIGNAL sid='s12'>by</SIGNAL> \n\
        <TIMEX3 tid='t10' type='DATE' value='1989-12-31' temporalFunction='true' functionInDocument='NONE' anchorTimeID='t9'>year-end</TIMEX3>")
    cls()
    
    print("Next in the annotations, we have the Event Instances and Links:\n")
    print("\
    <MAKEINSTANCE eventID='e19' eiid='ei79' tense='NONE' aspect='NONE' polarity='POS' pos='NOUN'/> \n\
    <MAKEINSTANCE eventID='e4' eiid='ei76' tense='PAST' aspect='NONE' polarity='POS' pos='VERB'/> \n\
    <MAKEINSTANCE eventID='e5' eiid='ei77' tense='PRESENT' aspect='NONE' polarity='POS' pos='VERB'/> \n\
    <MAKEINSTANCE eventID='e1' eiid='ei73' tense='PAST' aspect='NONE' polarity='POS' pos='VERB'/> \n\
    <MAKEINSTANCE eventID='e20' eiid='ei81' tense='NONE' aspect='NONE' polarity='POS' pos='NOUN'/> \n\
    <MAKEINSTANCE eventID='e2' eiid='ei74' tense='PAST' aspect='NONE' polarity='POS' pos='VERB'/> \n\
    <MAKEINSTANCE eventID='e7' eiid='ei80' tense='PRESENT' aspect='NONE' polarity='POS' pos='VERB'/> \n\
    <MAKEINSTANCE eventID='e6' eiid='ei78' tense='INFINITIVE' aspect='NONE' polarity='POS' pos='VERB'/> \n\
    <MAKEINSTANCE eventID='e8' eiid='ei75' tense='NONE' aspect='NONE' polarity='POS' pos='NOUN'/> \n\n\
    <TLINK lid='l1' relType='BEFORE' eventInstanceID='ei80' relatedToTime='t10' signalID='s12'/> \n\
    <TLINK lid='l2' relType='BEFORE' eventInstanceID='ei73' relatedToTime='t9'/> \n\
    <TLINK lid='l3' relType='BEFORE' eventInstanceID='ei74' relatedToEventInstance='ei73'/> \n\
    <TLINK lid='l4' relType='AFTER' eventInstanceID='ei74' relatedToEventInstance='ei75'/> \n\
    <TLINK lid='l5' relType='SIMULTANEOUS' eventInstanceID='ei76' relatedToEventInstance='ei73'/> \n\
    <TLINK lid='l6' relType='ENDS' eventInstanceID='ei80' relatedToEventInstance='ei81'/> \n\n\
    <SLINK lid='l13' relType='MODAL' eventInstanceID='ei74' subordinatedEventInstance='ei75'/> \n\
    <SLINK lid='l7' relType='EVIDENTIAL' eventInstanceID='ei73' subordinatedEventInstance='ei74'/> \n\
    <SLINK lid='l8' relType='EVIDENTIAL' eventInstanceID='ei76' subordinatedEventInstance='ei77'/> \n\
    <SLINK lid='l9' relType='MODAL' eventInstanceID='ei77' subordinatedEventInstance='ei78'/> \n\
    <SLINK lid='l10' relType='FACTIVE' eventInstanceID='ei78' subordinatedEventInstance='ei79'/> \n\
    <SLINK lid='l11' relType='MODAL' eventInstanceID='ei77' subordinatedEventInstance='ei80'/>\n\n\
    <ALINK lid='l12' relType='CULMINATES' eventInstanceID='ei80' relatedToEventInstance='ei81'/>")
    cls()

    print("The parser discards unnecessary data and builds a set of nodes and links, which we will now explore...")
    cls()
    
    
    
    print("WSJ_0006.tml parsed nodes:\n")
    for node in wsj_0006.nodes:
        print("{}, ".format(node.get_id_str()), end="")
    print("\b\b\n\n")

    print("\nWSJ_0006.tml parsed links:\n")
    for link in wsj_0006.links:
        print("{} -> {}({}) -> {}".format(link.start_node.get_id_str(), link.rel_type, link.link_tag, link.related_to_node.get_id_str()))

    cls()
    print("Let's explore the partitioner...")
    cls()
    print("WSJ_0006.tml main partition nodes:\n")
    for node in wsj_0006.main_graphs[0].nodes:
        print(node.get_id_str(), end=", ")
    print("\b\b\n\n")

    print("\nWSJ006.tml subordinate partition nodes:\n")
    count = 1
    for partition in wsj_0006.subordination_graphs:
        print("partition {}: ".format(count), end="")
        count += 1
        for node in partition.nodes:
            print(node.get_id_str(), end=", ")
        print("\b\b")

    cls()

    print("Let's take a look at the indeterminacy detector's report...")
    cls()

    print("Indeterminacy score: {}%".format(round(wsj_0006.indeterminacy_score*100, 2)))
    print("Indeterminant Sections: {}".format(sorted(wsj_0006.indeterminant_sections)))
    print("Indeterminant Time points: ", end="")
    for tp in sorted(wsj_0006.indeterminant_time_points):
        print(tp, end=", ")
    print("\b\b")
    cls()

    print("Now, let's look at the culmination of TLEX, the extracted timelines...")
    cls()

    print("wsj_0006 Main Timeline: \n\t{}\n\n".format(wsj_0006.timeline))

    count = 0
    for timeline in wsj_0006.subordinate_timelines():
        print("Subordinate Timeline {}:\n\t{}".format(count, timeline))
        count += 1
        
    cls()
    print("  _______ _                 _                           __                                      _   _ \n\
 |__   __| |               | |                         / _|                                    | | (-)\n\
    | |  | |__   __ _ _ __ | | __  _   _  ___  _   _  | |_ ___  _ __   _   _  ___  _   _ _ __  | |_ _ _ __ ___   ___\n\
    | |  | '_ \\ / _` | '_ \\| |/ / | | | |/ _ \\| | | | |  _/ _ \\| '__| | | | |/ _ \\| | | | '__| | __| | '_ ` _ \\ / _ \\\n\
    | |  | | | | (_| | | | |   <  | |_| | (_) | |_| | | || (_) | |    | |_| | (_) | |_| | |    | |_| | | | | | |  __/\n\
    |_|  |_| |_|\\__,_|_| |_|_|\\_\\  \\__, |\\___/ \\__,_| |_| \\___/|_|     \\__, |\\___/ \\__,_|_|     \\__|_|_| |_| |_|\\___| \n\
                                    __/ |                               __/ |\n\
                                   |___/                               |___/                                         ")
    

