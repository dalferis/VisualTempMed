"""
Unit tests for the visualizer (timeView / textView / sceneItems).

These build a real TimeScene and TextScene from a TML string, exercising
the same pipeline as mainWindow.openTimeMlFile (Graph -> TLEX -> merge
suggested links -> DataModel -> scene). Qt runs on the offscreen platform
so no window is shown.

Command to run from the project root:
    python -m unittest unit_tests.test_visualizer

Boundary cases covered:
  - an EVENT with two MAKEINSTANCEs (multi-instance -> stacked satellites)
  - a link that targets a specific (non-first) instance
  - a document without a Document Creation Time (DCT)
  - a document with a DCT (overlay, DCT not drawn as an inline node)
  - two events linked to each other (single edge, right direction)
  - an SLINK is drawn exactly once (regression: it used to be drawn twice,
    once from graph.links and once from tlex.s_links)
"""
import os
# Must be set before any Qt import so QApplication can start headless.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest

from PySide6.QtWidgets import QApplication

from pytlex_core.data import Graph
from pytlex_core.algorithms import TLEX, Partitioner
from dataModel import DataModel
import timeView as tv
import textView as txv
import sceneItems as si


# --------------------------------------------------------------------------
# TML fixtures (inline so each case sits next to its assertions). Every
# MAKEINSTANCE carries polarity/pos/tense/aspect because pytlex's parser
# requires them (unlike the validator, which tolerates omissions).
# --------------------------------------------------------------------------

# EVENT e1 has two instances; each instance is anchored to a different date.
TML_TWO_INSTANCES = """<?xml version="1.0" encoding="UTF-8"?>
<TimeML>
  <TEXT>He <EVENT eid="e1" class="OCCURRENCE" stem="leave">left</EVENT> on <TIMEX3 tid="t1" type="DATE" value="1998-01-05" temporalFunction="false" functionInDocument="NONE">Monday</TIMEX3> and <TIMEX3 tid="t2" type="DATE" value="1998-01-06" temporalFunction="false" functionInDocument="NONE">Tuesday</TIMEX3>.</TEXT>
  <MAKEINSTANCE eiid="ei1" eventID="e1" tense="PAST" aspect="NONE" polarity="POS" pos="VERB"/>
  <MAKEINSTANCE eiid="ei2" eventID="e1" tense="PAST" aspect="NONE" polarity="POS" pos="VERB"/>
  <TLINK lid="l1" relType="IS_INCLUDED" eventInstanceID="ei1" relatedToTime="t1"/>
  <TLINK lid="l2" relType="IS_INCLUDED" eventInstanceID="ei2" relatedToTime="t2"/>
</TimeML>"""

# Two events, one TLINK between them, no Document Creation Time.
TML_NO_DCT = """<?xml version="1.0" encoding="UTF-8"?>
<TimeML>
  <TEXT>The <EVENT eid="e1" class="OCCURRENCE" stem="admit">admission</EVENT> was before the <EVENT eid="e2" class="OCCURRENCE" stem="operate">surgery</EVENT>.</TEXT>
  <MAKEINSTANCE eiid="ei1" eventID="e1" tense="PAST" aspect="NONE" polarity="POS" pos="NOUN"/>
  <MAKEINSTANCE eiid="ei2" eventID="e2" tense="PAST" aspect="NONE" polarity="POS" pos="NOUN"/>
  <TLINK lid="l1" relType="BEFORE" eventInstanceID="ei1" relatedToEventInstance="ei2"/>
</TimeML>"""

# Same as above plus a CREATION_TIME TIMEX3.
TML_WITH_DCT = """<?xml version="1.0" encoding="UTF-8"?>
<TimeML>
  <TEXT><TIMEX3 tid="t0" type="DATE" value="1998-01-01" temporalFunction="false" functionInDocument="CREATION_TIME">Jan 1 1998</TIMEX3> The <EVENT eid="e1" class="OCCURRENCE" stem="admit">admission</EVENT>.</TEXT>
  <MAKEINSTANCE eiid="ei1" eventID="e1" tense="PAST" aspect="NONE" polarity="POS" pos="NOUN"/>
</TimeML>"""

# A document whose reference times are a PUBLICATION_TIME and a CREATION_TIME
# (no creation-time-only assumption): both belong in the header overlay.
TML_DOC_FUNCTIONS = """<?xml version="1.0" encoding="UTF-8"?>
<TimeML>
  <TIMEX3 tid="t0" type="DATE" value="1989-11-01" temporalFunction="false" functionInDocument="CREATION_TIME">Nov 1</TIMEX3>
  <TIMEX3 tid="t1" type="DATE" value="1989-11-02" temporalFunction="false" functionInDocument="PUBLICATION_TIME">Nov 2</TIMEX3>
  <TEXT>The <EVENT eid="e1" class="OCCURRENCE" stem="admit">admission</EVENT>.</TEXT>
  <MAKEINSTANCE eiid="ei1" eventID="e1" tense="PAST" aspect="NONE" polarity="POS" pos="NOUN"/>
</TimeML>"""

# Only a PUBLICATION_TIME, no creation time (e.g. wsj_0150).
TML_PUBLICATION_ONLY = """<?xml version="1.0" encoding="UTF-8"?>
<TimeML>
  <TIMEX3 tid="t0" type="DATE" value="1989-11-02" temporalFunction="false" functionInDocument="PUBLICATION_TIME">11/02/89</TIMEX3>
  <TEXT>The <EVENT eid="e1" class="OCCURRENCE" stem="admit">admission</EVENT>.</TEXT>
  <MAKEINSTANCE eiid="ei1" eventID="e1" tense="PAST" aspect="NONE" polarity="POS" pos="NOUN"/>
</TimeML>"""

# An SLINK between two events. After partitioning, TLEX restores graph.links
# (so the SLINK is in graph.links) AND keeps it in tlex.s_links; the planner
# must not draw it twice.
TML_SLINK = """<?xml version="1.0" encoding="UTF-8"?>
<TimeML>
  <TEXT>He <EVENT eid="e1" class="REPORTING" stem="say">said</EVENT> it would <EVENT eid="e2" class="OCCURRENCE" stem="rain">rain</EVENT>.</TEXT>
  <MAKEINSTANCE eiid="ei1" eventID="e1" tense="PAST" aspect="NONE" polarity="POS" pos="VERB"/>
  <MAKEINSTANCE eiid="ei2" eventID="e2" tense="NONE" aspect="NONE" polarity="POS" pos="VERB"/>
  <SLINK lid="l1" relType="EVIDENTIAL" eventInstanceID="ei1" subordinatedEventInstance="ei2"/>
</TimeML>"""


def buildScenes(tml):
    """Reproduces mainWindow.openTimeMlFile's pipeline and returns
    (time_scene, text_scene) for the given TML string."""
    # pytlex's Partitioner keeps SLinks in a module-level set that leaks
    # across files; mainWindow clears it between loads, so we do too.
    Partitioner.single_links.clear()
    graph = Graph.Graph(time_ml_string=tml)
    tlex = TLEX.TLEX(graph=graph)
    for link in tlex.suggested_links or []:
        graph.links.setdefault(link.get_id_str(), link)
    model = DataModel(graph, tlex)
    return tv.TimeView(model).scene, txv.TextView(model).scene


def edgesOf(scene):
    return [it for it in scene.items() if isinstance(it, si.LaneEdgeItem)]


def edgesBetween(scene, start_node, related_to_node):
    return [e for e in edgesOf(scene)
            if e.link.start_node == start_node and e.link.related_to_node == related_to_node]


class VisualizerTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # One QApplication for the whole test run.
        cls._app = QApplication.instance() or QApplication([])

    # ---- EVENT with two MAKEINSTANCEs -----------------------------------

    def testTwoInstancesAreSeparateNodesInTimeView(self):
        time_scene, _ = buildScenes(TML_TWO_INSTANCES)
        self.assertIn("eiid1", time_scene.nodes)
        self.assertIn("eiid2", time_scene.nodes)

    def testTwoInstancesAreSeparateNodesInTextView(self):
        _, text_scene = buildScenes(TML_TWO_INSTANCES)
        self.assertIn("eiid1", text_scene.nodes)
        self.assertIn("eiid2", text_scene.nodes)

    def testTwoInstancesStackInTextView(self):
        _, text_scene = buildScenes(TML_TWO_INSTANCES)
        primary = text_scene.nodes["eiid1"]
        satellite = text_scene.nodes["eiid2"]
        # The primary keeps its text position; the satellite is stacked below.
        self.assertTrue(getattr(primary, "_has_stacked_below", False))
        self.assertTrue(getattr(satellite, "_has_stacked_above", False))
        # Stacking pushes the following text rows down.
        self.assertTrue(text_scene._line_extra_height)
        # Satellite sits below and staggered right of the primary.
        self.assertGreater(satellite.pos().y(), primary.pos().y())
        self.assertGreater(satellite.pos().x(), primary.pos().x())

    def testLinkTargetsCorrectInstanceInTextView(self):
        # l1 anchors ei1->t1, l2 anchors ei2->t2; each edge must reach the
        # right instance even though both share the EVENT text "left".
        _, text_scene = buildScenes(TML_TWO_INSTANCES)
        self.assertEqual(len(edgesBetween(text_scene, "eiid1", "t1")), 1)
        self.assertEqual(len(edgesBetween(text_scene, "eiid2", "t2")), 1)
        # The wrong pairings must NOT exist.
        self.assertEqual(len(edgesBetween(text_scene, "eiid1", "t2")), 0)
        self.assertEqual(len(edgesBetween(text_scene, "eiid2", "t1")), 0)

    # ---- Document Creation Time -----------------------------------------

    def testNoDctHasNoOverlay(self):
        _, text_scene = buildScenes(TML_NO_DCT)
        self.assertEqual(text_scene._doc_function_boxes, [])

    def testNoDctScenesStillBuild(self):
        time_scene, text_scene = buildScenes(TML_NO_DCT)
        self.assertIn("eiid1", time_scene.nodes)
        self.assertIn("eiid2", time_scene.nodes)
        self.assertIn("eiid1", text_scene.nodes)
        self.assertIn("eiid2", text_scene.nodes)

    def testDctProducesOverlay(self):
        _, text_scene = buildScenes(TML_WITH_DCT)
        self.assertEqual(len(text_scene._doc_function_boxes), 1)

    def testDctDrawnAsInlineNodeWhenInBody(self):
        # A CREATION_TIME TIMEX3 that appears in the text body is rendered
        # as an inline node (in addition to the header overlay). This is the
        # case for E3C documents where the annotators marked an in-body
        # TIMEX3 as DOCTIME (e.g. EN100022, EN100024, EN100466).
        _, text_scene = buildScenes(TML_WITH_DCT)
        self.assertIn("t0", text_scene.nodes)

    def testMultipleDocFunctionsInHeader(self):
        # CREATION_TIME and PUBLICATION_TIME both get a header box, in
        # distinct colours, creation time first.
        _, text_scene = buildScenes(TML_DOC_FUNCTIONS)
        boxes = text_scene._doc_function_boxes
        self.assertEqual(len(boxes), 2)
        labels = [b[1] for b in boxes]
        self.assertIn("Document Creation Time: 1989-11-01", labels[0])
        self.assertIn("Publication Time: 1989-11-02", labels[1])
        colors = {b[3].name() for b in boxes}
        self.assertEqual(len(colors), 2)  # distinct colours

    def testPublicationOnlyProducesOverlay(self):
        # A document with only a PUBLICATION_TIME (no creation time) still
        # shows a header box (previously it showed nothing).
        _, text_scene = buildScenes(TML_PUBLICATION_ONLY)
        self.assertEqual(len(text_scene._doc_function_boxes), 1)
        self.assertIn("Publication Time", text_scene._doc_function_boxes[0][1])
        self.assertNotIn("t0", text_scene.nodes)

    # ---- Two events linked to each other --------------------------------

    def testTwoLinkedEventsSingleEdgeTimeView(self):
        time_scene, _ = buildScenes(TML_NO_DCT)
        edges = edgesBetween(time_scene, "eiid1", "eiid2")
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].link.rel_type, "BEFORE")

    def testTwoLinkedEventsSingleEdgeTextView(self):
        _, text_scene = buildScenes(TML_NO_DCT)
        edges = edgesBetween(text_scene, "eiid1", "eiid2")
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].link.rel_type, "BEFORE")

    # ---- Link not duplicated --------------------------------------------

    def testSlinkDrawnOnceTimeView(self):
        time_scene, _ = buildScenes(TML_SLINK)
        slinks = [e for e in edgesOf(time_scene) if e.link.link_tag == "SLINK"]
        self.assertEqual(len(slinks), 1, [e.link.get_id_str() for e in slinks])

    def testSlinkDrawnOnceTextView(self):
        _, text_scene = buildScenes(TML_SLINK)
        slinks = [e for e in edgesOf(text_scene) if e.link.link_tag == "SLINK"]
        self.assertEqual(len(slinks), 1, [e.link.get_id_str() for e in slinks])


if __name__ == "__main__":
    unittest.main()
