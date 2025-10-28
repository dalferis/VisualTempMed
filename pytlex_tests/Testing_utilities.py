import random
from typing import Optional

from pytlex_core.data.Event import Event
from pytlex_core.data.Instance import Instance
from pytlex_core.data.TimeX import TimeX
from pytlex_core.data.Signal import Signal
from pytlex_core.data.Link import Link
from pytlex_core.data import Graph

next_id = 0

failed_parse = ['ABC19980304.1830.1636.tml', 'APW19980213.1320.tml', 'APW19980227.0468.tml', 'APW19980227.0489.tml']

def consistent_graph_1() -> Graph:
    graph = Graph.Graph()

    node1 = TimeX(50, "FUTURE_REF", True, "next wednesday")
    node2 = TimeX(51, "FUTURE_REF", True, "next thursday")
    link1 = Link(50, "TLINK", "BEFORE", node1.get_id_str(), node2.get_id_str())


    graph.nodes.update({node1.get_id_str() : node1})
    graph.nodes.update({node2.get_id_str(): node2})
    graph.links.update({link1.get_id_str() : link1})

    return graph


def consistent_graph_2() -> Graph:
    graph = Graph.Graph()

    node1 = TimeX(50, "FUTURE_REF", True, "next wednesday")
    node2 = TimeX(51, "FUTURE_REF", True, "next thursday")
    node3 = TimeX(52, "FUTURE_REF", True, "next friday")
    link1 = Link(50, "TLINK", "BEFORE", node1.get_id_str(), node2.get_id_str())
    link2 = Link(51, "TLINK", "BEFORE", node2.get_id_str(), node3.get_id_str())

    graph.nodes.update({node1.get_id_str(): node1})
    graph.nodes.update({node2.get_id_str(): node2})
    graph.nodes.update({node3.get_id_str(): node3})

    graph.links.update({link1.get_id_str(): link1})
    graph.links.update({link2.get_id_str(): link2})

    return graph


def consistent_graph_3() -> Graph:
    graph = Graph.Graph()

    event1 = Event(10, "REPORTING", "Test Stem1")
    event2 = Event(11, "PERCEPTION", "Test Stem2")

    node1 = TimeX(50, "FUTURE_REF", True, "next wednesday")
    node2 = TimeX(51, "FUTURE_REF", True, "next thursday")
    node3 = Instance(52, event1.get_id_str(), "PAST", "PROGRESSIVE", "NOUN", "POS")
    node4 = Instance(53, event2.get_id_str(), "PRESENT", "PERFECTIVE", "VERB", "POS")

    link1 = Link(54, "TLINK", "INCLUDES", node1.get_id_str(), node3.get_id_str())
    link2 = Link(55, "ALINK", "INITIATES", node4.get_id_str(), node2.get_id_str())
    link3 = Link(56, "TLINK", "AFTER", node2.get_id_str(), node1.get_id_str())
    graph.events.update({event1.get_id_str(), event1})
    graph.events.update({event2.get_id_str(), event2})

    graph.nodes.update({node1.get_id_str(): node1})
    graph.nodes.update({node2.get_id_str(): node2})
    graph.nodes.update({node3.get_id_str(): node3})
    graph.nodes.update({node4.get_id_str(): node4})

    graph.links.update({link1.get_id_str(): link1})
    graph.links.update({link2.get_id_str(): link2})
    graph.links.update({link3.get_id_str(): link3})

    return graph


def consistent_graph_4() -> Graph:
    graph = Graph.Graph()

    node1 = TimeX(50, "FUTURE_REF", True, "next wednesday")
    node2 = TimeX(51, "FUTURE_REF", True, "next thursday")

    event1 = Event(10, "REPORTING", "Test Stem1")
    node3 = Instance(52, event1.get_id_str(), "PAST", "PROGRESSIVE", "NOUN", "POS")

    link1 = Link(54, "TLINK", "BEFORE", node1.get_id_str(), node2.get_id_str())
    link2 = Link(55, "SLINK", "MODAL", node2.get_id_str(), node3.get_id_str())

    graph.events.update({event1.get_id_str(), event1})

    graph.nodes.update({node1.get_id_str(): node1})
    graph.nodes.update({node2.get_id_str(): node2})
    graph.nodes.update({node3.get_id_str(): node3})

    graph.links.update({link1.get_id_str(): link1})
    graph.links.update({link2.get_id_str(): link2})

    return graph


def consistent_graph_5() -> Graph:
    graph = Graph.Graph()

    node1 = TimeX(50, "FUTURE_REF", True, "next wednesday")
    node2 = TimeX(51, "FUTURE_REF", True, "next thursday")

    event1 = Event(10, "REPORTING", "Test Stem1")
    node3 = Instance(52, event1.get_id_str(), "PAST", "PROGRESSIVE", "NOUN", "POS")
    node4 = TimeX(51, "FUTURE_REF", True, "some imaginary time")

    link1 = Link(54, "TLINK", "BEFORE", node1.get_id_str(), node2.get_id_str())
    link2 = Link(55, "SLINK", "MODAL", node2.get_id_str(), node3.get_id_str())
    link3 = Link(56, "TLINK", "AFTER", node3.get_id_str(), node4.get_id_str())

    graph.events.update({event1.get_id_str(), event1})

    graph.nodes.update({node1.get_id_str(): node1})
    graph.nodes.update({node2.get_id_str(): node2})
    graph.nodes.update({node3.get_id_str(): node3})
    graph.nodes.update({node4.get_id_str(): node4})

    graph.links.update({link1.get_id_str(): link1})
    graph.links.update({link2.get_id_str(): link2})
    graph.links.update({link3.get_id_str(): link3})

    return graph


def consistent_graph_6() -> Graph:
    t50 = test_timex(50)
    t51 = test_timex()
    t52 = test_timex()
    t53 = test_timex()
    t54 = test_timex()
    t55 = test_timex()
    t56 = test_timex()

    link1 = Link(1, "TLINK", "BEFORE", t50.get_id_str(), t51.get_id_str())
    link2 = Link(2, "TLINK", "BEFORE", t51.get_id_str(), t52.get_id_str())
    link3 = Link(3, "SLINK", "MODAL", t51.get_id_str(), t53.get_id_str())
    link4 = Link(4, "TLINK", "INCLUDES", t53.get_id_str(), t54.get_id_str())
    link5 = Link(5, "SLINK", "MODAL", t51.get_id_str(), t55.get_id_str())
    link6 = Link(6, "TLINK", "INCLUDES", t55.get_id_str(), t56.get_id_str())

    nodes = {t50, t51, t52, t53, t54, t55, t56}
    links = {link1, link2, link3, link4, link5, link6}

    return Graph.Graph(nodes=nodes, links=links)


def consistent_graph_7() -> Graph:
    t1 = test_timex(1)
    t2 = test_timex()
    t3 = test_timex()
    t4 = test_timex()
    t5 = test_timex()
    t6 = test_timex()
    t7 = test_timex()
    t8 = test_timex()
    t9 = test_timex()
    t10 = test_timex()
    t11 = test_timex()
    t12 = test_timex()
    t13 = test_timex()
    t14 = test_timex()
    t15 = test_timex()

    link1 = Link(1, "TLINK", "BEFORE", t1.get_id_str(), t2.get_id_str())
    link2 = Link(2, "TLINK", "BEFORE", t2.get_id_str(), t13.get_id_str())
    link3 = Link(3, "SLINK", "FACTIVE", t2.get_id_str(), t13.get_id_str())
    link4 = Link(4, "TLINK", "BEFORE", t2.get_id_str(), t3.get_id_str())
    link5 = Link(5, "SLINK", "COUNTER_FACTIVE", t2.get_id_str(), t5.get_id_str())
    link6 = Link(6, "TLINK", "BEFORE", t5.get_id_str(), t6.get_id_str())
    link7 = Link(7, "TLINK", "IDENTITY", t3.get_id_str(), t4.get_id_str())
    link8 = Link(8, "SLINK", "MODAL", t3.get_id_str(), t7.get_id_str())
    link9 = Link(9, "SLINK", "MODAL", t4.get_id_str(), t8.get_id_str())
    link10 = Link(10, "TLINK", "IDENTITY", t7.get_id_str(), t8.get_id_str())
    link11 = Link(11, "TLINK", "INCLUDES", t13.get_id_str(), t14.get_id_str())
    link12 = Link(12, "TLINK", "ENDED_BY", t14.get_id_str(), t15.get_id_str())
    link13 = Link(13, "TLINK", "DURING", t8.get_id_str(), t9.get_id_str())
    link14 = Link(14, "TLINK", "DURING", t9.get_id_str(), t10.get_id_str())
    link15 = Link(15, "TLINK", "DURING", t10.get_id_str(), t11.get_id_str())
    link16 = Link(16, "SLINK", "EVIDENTIAL", t11.get_id_str(), t12.get_id_str())
    link17 = Link(17, "TLINK", "IBEFORE", t11.get_id_str(), t12.get_id_str())

    nodes = {t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15}

    links = {link1, link2, link3, link4, link5, link6
        , link7, link8, link9, link10, link11, link12
        , link13, link14, link15, link16, link17}

    return Graph.Graph(nodes=nodes, links=links)


def consistent_graph_8() -> Graph:
    t1 = test_timex(1)
    t2 = test_timex()
    t3 = test_timex()
    t4 = test_timex()
    t5 = test_timex()
    t6 = test_timex()
    t7 = test_timex()
    t8 = test_timex()
    t9 = test_timex()
    t10 = test_timex()
    t11 = test_timex()
    t12 = test_timex()
    t13 = test_timex()

    link1 = Link(1, "TLINK", "IBEFORE", t1.get_id_str(), t2.get_id_str())
    link2 = Link(2, "TLINK", "ENDS", t2.get_id_str(), t3.get_id_str())
    link3 = Link(3, "TLINK", "BEGINS", t1.get_id_str(), t3.get_id_str())
    link4 = Link(4, "TLINK", "BEGINS", t2.get_id_str(), t4.get_id_str())
    link5 = Link(5, "TLINK", "ENDS", t5.get_id_str(), t4.get_id_str())
    link6 = Link(6, "TLINK", "ENDS", t5.get_id_str(), t6.get_id_str())
    link7 = Link(7, "TLINK", "BEGINS", t3.get_id_str(), t6.get_id_str())
    link8 = Link(8, "TLINK", "AFTER", t7.get_id_str(), t6.get_id_str())
    link9 = Link(9, "TLINK", "AFTER", t8.get_id_str(), t7.get_id_str())
    link10 = Link(10, "TLINK", "BEGUN_BY", t9.get_id_str(), t7.get_id_str())
    link11 = Link(11, "TLINK", "ENDED_BY", t9.get_id_str(), t8.get_id_str())
    link12 = Link(12, "TLINK", "ENDS", t9.get_id_str(), t10.get_id_str())
    link13 = Link(13, "TLINK", "IAFTER", t10.get_id_str(), t6.get_id_str())
    link14 = Link(14, "TLINK", "BEGUN_BY", t11.get_id_str(), t5.get_id_str())
    link15 = Link(15, "TLINK", "ENDS", t10.get_id_str(), t11.get_id_str())
    link16 = Link(16, "TLINK", "INCLUDES", t12.get_id_str(), t11.get_id_str())
    link17 = Link(17, "TLINK", "BEGINS", t13.get_id_str(), t12.get_id_str())
    link18 = Link(18, "TLINK", "IBEFORE", t13.get_id_str(), t5.get_id_str())
    link19 = Link(19, "TLINK", "INCLUDES", t4.get_id_str(), t13.get_id_str())

    nodes_set = {t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13}
    link_set = {link1, link2, link3, link4, link5, link6, link7, link8, link9, link10, link11, link12, link13,
                link14, link15, link16, link17, link18, link19}
    return Graph.Graph(nodes=nodes_set, links=link_set)


def consistent_graph_9() -> Graph:
    t1 = test_timex(1)
    t2 = test_timex()
    t3 = test_timex()
    t4 = test_timex()
    t5 = test_timex()
    t6 = test_timex()
    t7 = test_timex()
    t8 = test_timex()
    t9 = test_timex()

    link1 = Link(1, "TLINK", "BEGUN_BY", t1.get_id_str(), t2.get_id_str())
    link2 = Link(2, "TLINK", "IAFTER", t3.get_id_str(), t2.get_id_str())
    link3 = Link(3, "TLINK", "IAFTER", t4.get_id_str(), t3.get_id_str())
    link4 = Link(4, "TLINK", "ENDS", t4.get_id_str(), t1.get_id_str())
    link5 = Link(5, "TLINK", "ENDS", t4.get_id_str(), t5.get_id_str())
    link6 = Link(6, "TLINK", "BEGUN_BY", t5.get_id_str(), t3.get_id_str())
    link7 = Link(7, "TLINK", "INCLUDES", t2.get_id_str(), t6.get_id_str())
    link8 = Link(8, "TLINK", "ENDS", t7.get_id_str(), t2.get_id_str())
    link9 = Link(9, "TLINK", "IBEFORE", t6.get_id_str(), t7.get_id_str())
    link10 = Link(10, "TLINK", "IBEFORE", t7.get_id_str(), t8.get_id_str())
    link11 = Link(11, "TLINK", "IAFTER", t9.get_id_str(), t8.get_id_str())
    link12 = Link(12, "TLINK", "ENDS", t9.get_id_str(), t1.get_id_str())

    node_set = {t1, t2, t3, t4, t5, t6, t7, t8, t9}
    link_set = {link1, link2, link3, link4, link5, link6, link7, link8, link9, link10, link11, link12}

    return Graph.Graph(nodes=node_set, links=link_set)


def consistent_graph_10() -> Graph:
    t1 = test_timex(1)
    t2 = test_timex()
    t3 = test_timex()
    t4 = test_timex()
    t5 = test_timex()
    t6 = test_timex()
    t7 = test_timex()
    t8 = test_timex()

    link1 = Link(1, "TLINK", "IBEFORE", t1.get_id_str(), t2.get_id_str())
    link2 = Link(2, "TLINK", "ENDS", t2.get_id_str(), t3.get_id_str())
    link3 = Link(3, "TLINK", "BEGINS", t1.get_id_str(), t3.get_id_str())
    link4 = Link(4, "TLINK", "IAFTER", t4.get_id_str(), t3.get_id_str())
    link5 = Link(5, "TLINK", "ENDS", t4.get_id_str(), t5.get_id_str())
    link6 = Link(6, "TLINK", "BEGINS", t3.get_id_str(), t5.get_id_str())
    link7 = Link(7, "TLINK", "IDENTITY", t4.get_id_str(), t6.get_id_str())
    link8 = Link(8, "TLINK", "AFTER", t7.get_id_str(), t6.get_id_str())
    link9 = Link(9, "TLINK", "ENDS", t7.get_id_str(), t8.get_id_str())
    link10 = Link(10, "TLINK", "IAFTER", t8.get_id_str(), t6.get_id_str())

    node_set = {t1, t2, t3, t4, t5, t6, t7, t8}
    link_set = {link1, link2, link3, link4, link5, link6, link7, link8, link9, link10}

    return Graph.Graph(nodes=node_set, links=link_set)


def consistent_graph_11() -> Graph:
    t1 = test_timex(1)
    t2 = test_timex()
    t3 = test_timex()
    t4 = test_timex()
    t5 = test_timex()
    t6 = test_timex()
    t7 = test_timex()
    t8 = test_timex()
    t9 = test_timex()
    t10 = test_timex()
    t11 = test_timex()
    t12 = test_timex()
    t13 = test_timex()
    t14 = test_timex()
    t15 = test_timex()
    t16 = test_timex()
    t17 = test_timex()
    t18 = test_timex()
    t19 = test_timex()
    t20 = test_timex()
    t21 = test_timex()
    t22 = test_timex()
    t23 = test_timex()
    t24 = test_timex()
    t25 = test_timex()
    t26 = test_timex()

    l1 = Link(1, "TLINK", "BEFORE", t1.get_id_str(), t2.get_id_str())
    l2 = Link(2, "TLINK", "BEFORE", t3.get_id_str(), t2.get_id_str())
    l3 = Link(3, "TLINK", "AFTER", t4.get_id_str(), t5.get_id_str())
    l4 = Link(4, "TLINK", "SIMULTANEOUS", t6.get_id_str(), t7.get_id_str())
    l5 = Link(5, "TLINK", "IS_INCLUDED", t8.get_id_str(), t9.get_id_str())
    l6 = Link(6, "TLINK", "DURING", t10.get_id_str(), t2.get_id_str())
    l7 = Link(7, "ALINK", "INITIATES", t11.get_id_str(), t10.get_id_str())
    l8 = Link(8, "TLINK", "BEFORE", t12.get_id_str(), t2.get_id_str())
    l9 = Link(9, "TLINK", "BEFORE", t8.get_id_str(), t2.get_id_str())
    l10 = Link(10, "TLINK", "IS_INCLUDED", t13.get_id_str(), t9.get_id_str())
    l11 = Link(11, "TLINK", "AFTER", t14.get_id_str(), t2.get_id_str())
    l12 = Link(12, "TLINK", "INCLUDES", t9.get_id_str(), t3.get_id_str())
    l13 = Link(13, "TLINK", "AFTER", t18.get_id_str(), t5.get_id_str())
    l14 = Link(14, "TLINK", "AFTER", t11.get_id_str(), t15.get_id_str())
    l15 = Link(15, "TLINK", "BEFORE", t16.get_id_str(), t2.get_id_str())
    l16 = Link(16, "TLINK", "BEFORE", t17.get_id_str(), t19.get_id_str())
    l17 = Link(17, "TLINK", "AFTER", t7.get_id_str(), t14.get_id_str())
    l18 = Link(18, "TLINK", "BEFORE", t20.get_id_str(), t2.get_id_str())
    l19 = Link(19, "TLINK", "AFTER", t21.get_id_str(), t2.get_id_str())
    l20 = Link(20, "TLINK", "AFTER", t19.get_id_str(), t18.get_id_str())
    l21 = Link(21, "TLINK", "IDENTITY", t22.get_id_str(), t23.get_id_str())
    l22 = Link(22, "TLINK", "AFTER", t22.get_id_str(), t14.get_id_str())
    l23 = Link(23, "TLINK", "BEFORE", t13.get_id_str(), t2.get_id_str())
    l24 = Link(24, "TLINK", "INCLUDES", t19.get_id_str(), t16.get_id_str())
    l25 = Link(25, "TLINK", "AFTER", t11.get_id_str(), t24.get_id_str())
    l26 = Link(26, "TLINK", "IDENTITY", t5.get_id_str(), t1.get_id_str())
    l27 = Link(27, "TLINK", "BEFORE", t26.get_id_str(), t18.get_id_str())
    l28 = Link(28, "TLINK", "INCLUDES", t9.get_id_str(), t2.get_id_str())
    l29 = Link(29, "TLINK", "BEFORE", t17.get_id_str(), t18.get_id_str())
    l30 = Link(30, "TLINK", "INCLUDES", t18.get_id_str(), t14.get_id_str())
    l31 = Link(31, "TLINK", "AFTER", t25.get_id_str(), t14.get_id_str())
    l32 = Link(32, "TLINK", "INCLUDES", t17.get_id_str(), t2.get_id_str())

    return Graph.Graph({t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15, t16, t17, t18, t19, t20, t21, t22, t23, t24, t25, t26},
                       {l1, l2, l3, l4, l5, l6, l7, l8, l9, l10, l11, l12, l13, l14, l15, l16, l17, l18, l19, l20, l21, l22, l23, l24, l25, l26, l27, l28, l29, l30, l31, l32})


def wsj_0006() -> Graph:
    event1 = Event(1, "REPORTING", "test_stem")
    event2 = Event(2, "OCCURRENCE", "test_stem")
    event8 = Event(8, "OCCURRENCE", "test_stem")
    event4 = Event(4, "REPORTING", "test_stem")
    event5 = Event(5, "I_STATE", "test_stem")
    event6 = Event(6, "OCCURRENCE", "test_stem")
    event19 = Event(19, "OCCURRENCE", "test_stem")
    event7 = Event(7, "ASPECTUAL", "test_stem")
    event20 = Event(20, "OCCURRENCE", "test_stem")

    node79 = Instance(79, event19.get_id_str(), event19.event_class, "NONE", "NONE", "NOUN", "POS")
    node76 = Instance(76, event4.get_id_str(), event4.event_class, "PAST", "NONE", "VERB", "POS")
    node77 = Instance(77, event5.get_id_str(), event5.event_class, "PRESENT", "NONE", "VERB", "POS")
    node73 = Instance(73, event1.get_id_str(), event1.event_class, "PAST", "NONE", "VERB", "POS")
    node81 = Instance(81, event20.get_id_str(), event20.event_class, "NONE", "NONE", "NOUN", "POS")
    node74 = Instance(74, event2.get_id_str(), event2.event_class, "PAST", "NONE", "VERB", "POS")
    node80 = Instance(80, event7.get_id_str(), event7.event_class, "PRESENT", "NONE", "VERB", "POS")
    node78 = Instance(78, event6.get_id_str(), event6.event_class, "INFINITIVE", "NONE", "VERB", "POS")
    node75 = Instance(75, event8.get_id_str(), event8.event_class, "NONE", "NONE", "NOUN", "POS")

    node10 = TimeX(9, "1989-11-02", False, "11/02/89", "DATE", "NONE", "CREATION_TIME")
    node11 = TimeX(10, "1989-12-31", True, "year-end", "DATE", "NONE", "NONE", 9)

    signal1 = Signal(12, "by")

    link1 = Link(1, "TLINK", "BEFORE", node80.get_id_str(), node11.get_id_str(), signal1.get_id_str())
    link2 = Link(2, "TLINK", "BEFORE", node73.get_id_str(), node10.get_id_str())
    link3 = Link(3, "TLINK", "BEFORE", node74.get_id_str(), node73.get_id_str())
    link4 = Link(4, "TLINK", "AFTER", node74.get_id_str(), node75.get_id_str())
    link5 = Link(5, "TLINK", "SIMULTANEOUS", node76.get_id_str(), node73.get_id_str())
    link6 = Link(6, "TLINK", "ENDS", node80.get_id_str(), node81.get_id_str())

    link13 = Link(13, "SLINK", "MODAL", node74.get_id_str(), node75.get_id_str())
    link7 = Link(7, "SLINK", "EVIDENTIAL", node73.get_id_str(), node74.get_id_str())
    link8 = Link(8, "SLINK", "EVIDENTIAL", node76.get_id_str(), node77.get_id_str())
    link9 = Link(9, "SLINK", "MODAL", node77.get_id_str(), node78.get_id_str())
    link10 = Link(10, "SLINK", "FACTIVE", node78.get_id_str(), node79.get_id_str())
    link11 = Link(11, "SLINK", "MODAL", node77.get_id_str(), node80.get_id_str())

    link12 = Link(12, "ALINK", "CULMINATES", node80.get_id_str(), node81.get_id_str())

    events = {event1, event2, event8, event4, event5, event6, event19, event7, event20}
    nodes = {node79, node76, node77, node73, node81, node74, node80, node78, node75, node10, node11}
    links = {link1, link2, link3, link4, link5, link6, link7, link8, link9, link10, link11, link12, link13}

    graph = Graph.Graph(nodes, links, events)
    return graph


def wsj_1073() -> Graph:
    event2 = Event(2, "REPORTING", "say")
    event3 = Event(3, "OCCURRENCE", "purchase")
    event4 = Event(4, "OCCURRENCE", "pay")
    event9 = Event(9, "OCCURRENCE", "have")
    event30 = Event(30, "OCCURRENCE", "sale")

    node1989 = Instance(1989, event2.get_id_str(), event_class=event2.event_class, tense="PAST", aspect="NONE", pos="VERB", polarity="POS")
    node1990 = Instance(1990, event3.get_id_str(), event_class=event3.event_class,tense="PAST", aspect="NONE", pos="VERB", polarity="POS")
    node1991 = Instance(1991, event4.get_id_str(), event_class=event4.event_class,tense="PAST", aspect="NONE", pos="VERB", polarity="POS")
    node1992 = Instance(1992, event9.get_id_str(), event_class=event9.event_class,tense="PAST", aspect="PERFECTIVE", pos="VERB", polarity="POS")
    node1993 = Instance(1993, event30.get_id_str(), event_class=event30.event_class,tense="NONE", aspect="NONE", pos="NOUN", polarity="POS")

    node11 = TimeX(11, "1989-10-25", False, "10/25/89", "DATE", "NONE", "CREATION_TIME")
    node31 = TimeX(31, "1988", True, "last year", "DATE", "NONE", "NONE", 11)

    link1 = Link(1, "TLINK", "SIMULTANEOUS", node1992.get_id_str(), node1993.get_id_str(), None, "USER")
    link2 = Link(2, "TLINK", "BEFORE", node1991.get_id_str(), node11.get_id_str(), None, "USER")
    link3 = Link(3, "TLINK", "BEFORE", node1989.get_id_str(), node11.get_id_str(), None, "USER")
    link4 = Link(4, "TLINK", "BEFORE", node1992.get_id_str(), node11.get_id_str(), None, "USER")
    link5 = Link(5, "TLINK", "BEFORE", node1993.get_id_str(), node31.get_id_str(), None, "USER")

    link6 = Link(6, "SLINK", "EVIDENTIAL", node1989.get_id_str(), node1990.get_id_str())

    events = {event2, event3, event4, event9, event30}
    nodes = {node1989, node1990, node1991, node1992, node1993, node11, node31}
    links = {link1, link2, link3, link4, link5, link6}

    graph = Graph.Graph(nodes, links, events)

    return graph


def wsj_0555() -> Graph:
    event1 = Event(1, "REPORTING", "test_stem")
    event11 = Event(11, "STATE", "test_stem")
    event2 = Event(2, "I_ACTION", "test_stem")
    event4 = Event(4, "OCCURRENCE", "test_stem")
    event6 = Event(6, "REPORTING", "test_stem")
    event7 = Event(7, "STATE", "test_stem")

    node44 = Instance(44, event1.get_id_str(), event1.event_class, "PAST", "NONE", pos="VERB", polarity="POS")
    node49 = Instance(49, event7.get_id_str(), event7.event_class, "PRESENT", "NONE", pos="VERB", polarity="POS")
    node46 = Instance(46, event2.get_id_str(), event2.event_class, "PRESENT", "PERFECTIVE", pos="VERB", polarity="POS")
    node47 = Instance(47, event4.get_id_str(), event4.event_class, "INFINITIVE", "NONE", pos="VERB", polarity="POS")
    node45 = Instance(45, event11.get_id_str(), event11.event_class, "NONE", "NONE", pos="ADJECTIVE", polarity="POS")
    node48 = Instance(48, event6.get_id_str(), event6.event_class, "PAST", "NONE", pos="VERB", polarity="POS")

    node12 = TimeX(12, "1989-10-30", False, "10/30/89", "DATE", "NONE", "CREATION_TIME")
    node13 = TimeX(13, "2007-03-15", False, "March 15, 2007", "DATE", "NONE", "NONE")

    link1 = Link(1, "TLINK", "BEFORE", node44.get_id_str(), node12.get_id_str())
    link2 = Link(2, "TLINK", "ENDED_BY", node45.get_id_str(), node13.get_id_str())
    link3 = Link(3, "TLINK", "BEFORE", node46.get_id_str(), node44.get_id_str())
    link4 = Link(4, "TLINK", "IDENTITY", node48.get_id_str(), node44.get_id_str())

    link5 = Link(5, "SLINK", "EVIDENTIAL", node44.get_id_str(), node46.get_id_str())
    link6 = Link(6, "SLINK", "MODAL", node46.get_id_str(), node47.get_id_str())
    link7 = Link(7, "SLINK", "EVIDENTIAL", node48.get_id_str(), node49.get_id_str())

    events = {event1, event11, event2, event4, event6, event7}
    nodes = {node44, node49, node46, node47, node45, node48, node12, node13}
    links = {link1, link2, link3, link4, link5, link6, link7}

    graph = Graph.Graph(nodes, links, events)
    return graph


def wsj_0032_inconsistent() -> Graph:
    ei103 = test_instance(103)
    ei112 = test_instance(112)
    ei104 = test_instance(104)
    ei111 = test_instance(111)
    ei106 = test_instance(106)
    ei107 = test_instance(107)
    ei110 = test_instance(110)
    ei105 = test_instance(105)
    ei109 = test_instance(109)
    ei102 = test_instance(102)
    ei108 = test_instance(108)

    t13 = test_timex(13)
    t19 = test_timex(19)
    t18 = test_timex(18)
    t17 = test_timex(17)
    t21 = test_timex(21)

    nodes = {ei103, ei112, ei104, ei111, ei106, ei107, ei110, ei105,
             ei109, ei102, ei108, t13, t17, t18, t19, t21}

    link25 = Link(25, "TLINK", "IS_INCLUDED", ei106.get_id_str(), t13.get_id_str())
    link1 = Link(1, "TLINK", "IS_INCLUDED", ei110.get_id_str(), t13.get_id_str())
    link2 = Link(2, "TLINK", "AFTER", t13.get_id_str(), ei102.get_id_str())
    link3 = Link(3, "TLINK", "BEGINS", ei102.get_id_str(), ei103.get_id_str())
    link4 = Link(4, "TLINK", "IDENTITY", ei104.get_id_str(), ei103.get_id_str())
    link5 = Link(5, "TLINK", "BEFORE", ei104.get_id_str(), ei105.get_id_str())
    link6 = Link(6, "TLINK", "IS_INCLUDED", ei105.get_id_str(), t19.get_id_str())
    link7 = Link(7, "TLINK", "IDENTITY", t19.get_id_str(), t13.get_id_str())
    link8 = Link(8, "TLINK", "BEFORE", ei104.get_id_str(), ei107.get_id_str())
    link9 = Link(9, "TLINK", "ENDED_BY", ei107.get_id_str(), t18.get_id_str())
    link10 = Link(10, "TLINK", "INCLUDES", t17.get_id_str(), t13.get_id_str())
    link11 = Link(11, "TLINK", "INCLUDES", t17.get_id_str(), ei108.get_id_str())
    link12 = Link(12, "TLINK", "IDENTITY", ei109.get_id_str(), ei104.get_id_str())
    link13 = Link(13, "TLINK", "BEGUN_BY", ei109.get_id_str(), ei110.get_id_str())
    link14 = Link(14, "TLINK", "AFTER", ei110.get_id_str(), ei112.get_id_str())
    link15 = Link(15, "TLINK", "BEFORE", ei112.get_id_str(), ei111.get_id_str())
    link16 = Link(16, "TLINK", "SIMULTANEOUS", ei111.get_id_str(), t21.get_id_str())
    link17 = Link(17, "TLINK", "BEFORE", t21.get_id_str(), t13.get_id_str())

    link18 = Link(18, "SLINK", "EVIDENTIAL", ei111.get_id_str(), ei112.get_id_str())
    link21 = Link(21, "SLINK", "FACTIVE", ei110.get_id_str(), ei112.get_id_str())
    link22 = Link(22, "SLINK", "EVIDENTIAL", ei105.get_id_str(), ei104.get_id_str())
    link23 = Link(23, "SLINK", "MODAL", ei106.get_id_str(), ei107.get_id_str())

    link19 = Link(19, "ALINK", "INITIATES", ei102.get_id_str(), ei103.get_id_str())

    links = {link1, link2, link3, link4, link5, link6, link7, link8, link9, link10, link11, link12,
             link13, link14, link15, link16, link17, link18, link19, link21, link22, link23, link25}

    return Graph.Graph(nodes=nodes, links=links)


def inconsistent_graph_1_self_loop() -> Graph:
    graph = Graph.Graph()

    node1 = TimeX(50, "FUTURE_REF", True, "next wednesday")
    node2 = TimeX(51, "FUTURE_REF", True, "next thursday")

    graph.nodes.add(node1)
    graph.nodes.add(node2)

    link1 = Link(52, "SLINK", "MODAL", node1.get_id_str(), node2.get_id_str())
    link2 = Link(53, "TLINK", "INCLUDES", node2.get_id_str(), node2.get_id_str())

    graph.links.add(link1)
    graph.links.add(link2)

    return graph


def inconsistent_graph_2_self_loop() -> Graph:
    graph = Graph.Graph()

    node1 = TimeX(50, "FUTURE_REF", True, "next wednesday")
    graph.nodes.add(node1)
    graph.links.add(Link(51, "TLINK", "BEFORE", node1.get_id_str(), node1.get_id_str()))

    return graph


def inconsistent_graph_3() -> Graph:
    graph = Graph.Graph()

    node1 = test_timex()
    node2 = test_timex()
    node3 = test_timex()

    link1 = Link(1, "TLINK", "BEFORE", node1.get_id_str(), node2.get_id_str())
    link2 = Link(2, "TLINK", "BEFORE", node2.get_id_str(), node3.get_id_str())
    link3 = Link(3, "TLINK", "BEFORE", node3.get_id_str(), node1.get_id_str())

    node_set = {node1, node2, node3}
    link_set = {link1, link2, link3}

    return Graph.Graph(nodes=node_set, links=link_set)


def inconsistent_graph_4() -> Graph:
    graph = Graph.Graph()

    node1 = test_timex()
    node2 = test_timex()
    node3 = test_timex()
    node4 = test_timex(49)

    link1 = Link(1, "TLINK", "BEFORE", node1.get_id_str(), node2.get_id_str())
    link2 = Link(2, "TLINK", "BEFORE", node2.get_id_str(), node3.get_id_str())
    link3 = Link(3, "TLINK", "BEFORE", node3.get_id_str(), node1.get_id_str())
    link4 = Link(4, "SLINK", "MODAL", node4.get_id_str(), node1.get_id_str())

    node_set = {node1, node2, node3, node4}
    link_set = {link1, link2, link3, link4}

    return Graph.Graph(nodes=node_set, links=link_set)


def inconsistent_graph_5() -> Graph:

    node1 = test_timex()
    node2 = test_timex()
    node3 = test_timex()
    node4 = test_timex()
    node5 = test_timex()
    node6 = test_timex()
    node7 = test_timex()

    link1 = Link(1, "TLINK", "INCLUDES", node1.get_id_str(), node2.get_id_str())
    link2 = Link(2, "TLINK", "BEFORE", node2.get_id_str(), node3.get_id_str())
    link3 = Link(3, "TLINK", "BEFORE", node3.get_id_str(), node4.get_id_str())
    link4 = Link(4, "TLINK", "BEFORE", node4.get_id_str(), node2.get_id_str())
    link5 = Link(5, "TLINK", "ENDS", node3.get_id_str(), node5.get_id_str())
    link6 = Link(6, "TLINK", "AFTER", node5.get_id_str(), node6.get_id_str())
    link7 = Link(7, "TLINK", "BEGINS", node6.get_id_str(), node7.get_id_str())
    link7 = Link(7, "TLINK", "AFTER", node6.get_id_str(), node7.get_id_str())

    node_set = {node1, node2, node3, node4, node5, node6, node7}
    link_set = {link1, link2, link3, link4, link5, link6, link7}

    return Graph.Graph(nodes=node_set, links=link_set)


def inconsistent_graph_6() -> Graph:
    node1 = test_timex()
    node2 = test_timex()

    link1 = Link(1, "TLINK", "INCLUDES", node1.get_id_str(), node2.get_id_str())
    link2 = Link(2, "TLINK", "ENDED_BY", node1.get_id_str(), node2.get_id_str())

    node_set = {node1, node2}
    link_set = {link1, link2}

    return Graph.Graph(nodes=node_set, links=link_set)


def inconsistent_graph_7() -> Graph:
    node1 = test_timex()
    node2 = test_timex()
    node3 = test_timex()

    link1 = Link(1, "TLINK", "BEFORE", node1.get_id_str(), node2.get_id_str())
    link2 = Link(2, "TLINK", "IAFTER", node2.get_id_str(), node3.get_id_str())
    link3 = Link(3, "TLINK", "ENDED_BY", node1.get_id_str(), node3.get_id_str())

    node_set = {node1, node2, node3}
    link_set = {link1, link2, link3}

    return Graph.Graph(nodes=node_set, links=link_set)


def indeterminant_graph_1() -> Graph:
    node1 = test_timex()
    node2 = test_timex()
    node3 = test_timex()
    node4 = test_timex()
    node5 = test_timex()

    link1 = Link(1, "TLINK", "BEFORE", node1.get_id_str(), node2.get_id_str())
    link2 = Link(2, "TLINK", "BEFORE", node1.get_id_str(), node3.get_id_str())
    link3 = Link(3, "TLINK", "BEFORE", node2.get_id_str(), node4.get_id_str())
    link4 = Link(4, "TLINK", "BEFORE", node3.get_id_str(), node4.get_id_str())
    link5 = Link(5, "TLINK", "BEFORE", node4.get_id_str(), node5.get_id_str())

    node_set = {node1, node2, node3, node4, node5}
    link_set = {link1, link2, link3, link4, link5}

    return Graph.Graph(nodes=node_set, links=link_set)


def test_timex(tid: Optional[int] = None):
    global next_id
    if tid is None:
        next_id += 1
    else:
        next_id = tid
    return TimeX(next_id, "Test Value", True, "Test Phrase")


def test_signal(sid: Optional[int] = None):
    global next_id
    if sid is None:
        next_id += 1
    else:
        next_id = sid
    return Signal(next_id, "Test Signal")


def test_event(eid: Optional[int] = None):
    global next_id
    if eid is None:
        next_id += 1
    else:
        next_id = eid
    return Event(next_id, "REPORTING", "Test Stem")


def test_instance(eiid: Optional[int] = None):
    global next_id
    if eiid is None:
        next_id += 1
    else:
        next_id = eiid
    return Instance(next_id, test_event().get_id_str(), "PAST", "NONE", "NOUN", "POS")


def _inconsistent_functions() -> list[str]:
    graph_functions = []

    graph_functions.append('inconsistent_graph_1_self_loop')
    graph_functions.append('inconsistent_graph_2_self_loop')
    graph_functions.append('inconsistent_graph_3')
    graph_functions.append('inconsistent_graph_4')
    graph_functions.append('inconsistent_graph_5')
    graph_functions.append('inconsistent_graph_6')
    graph_functions.append('inconsistent_graph_7')

    return  graph_functions


def _consistent_functions() -> list[str]:
    graph_functions = []

    graph_functions.append('consistent_graph_1')
    graph_functions.append('consistent_graph_2')
    graph_functions.append('consistent_graph_3')
    graph_functions.append('consistent_graph_4')
    graph_functions.append('consistent_graph_5')
    graph_functions.append('consistent_graph_6')
    graph_functions.append('consistent_graph_7')
    graph_functions.append('consistent_graph_8')
    graph_functions.append('consistent_graph_9')
    graph_functions.append('consistent_graph_10')

    return graph_functions


def random_graph(consistent: Optional[bool] = None) -> Graph:
    if consistent is not None:
        if consistent:
            return globals()[random.choice(_consistent_functions())]()
        elif not consistent:
            return globals()[random.choice(_inconsistent_functions())]
    else:
        return globals()[random.choice(_consistent_functions() + _inconsistent_functions())]


def all_graphs(consistent: Optional[bool] = None) -> list[Graph]:
    if consistent is not None:
        if consistent:
            return [globals()[function]() for function in _consistent_functions()]
        else:
            return [globals()[function]() for function in _inconsistent_functions()]
    else:
        return [globals()[function]() for function in _consistent_functions() + _inconsistent_functions()]


if __name__ == '__main__':
    print(len(_consistent_functions()))
    print(len(_inconsistent_functions()))
    print(len(_consistent_functions() + _inconsistent_functions()))
