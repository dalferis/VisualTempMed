"""
Unit tests for the visualizer (timeView / textView / sceneItems).

These build a real TimeScene and TextScene from a TML file, exercising
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


TEST_TML_DIR = os.path.join(os.path.dirname(__file__), "test_visualizer_tml")


def readTml(name):
    with open(os.path.join(TEST_TML_DIR, name), encoding="utf-8") as f:
        return f.read()


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
        time_scene, _ = buildScenes(readTml("two_instances.tml"))
        self.assertIn("eiid1", time_scene.nodes)
        self.assertIn("eiid2", time_scene.nodes)

    def testTwoInstancesAreSeparateNodesInTextView(self):
        _, text_scene = buildScenes(readTml("two_instances.tml"))
        self.assertIn("eiid1", text_scene.nodes)
        self.assertIn("eiid2", text_scene.nodes)

    def testTwoInstancesStackInTextView(self):
        _, text_scene = buildScenes(readTml("two_instances.tml"))
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
        _, text_scene = buildScenes(readTml("two_instances.tml"))
        self.assertEqual(len(edgesBetween(text_scene, "eiid1", "t1")), 1)
        self.assertEqual(len(edgesBetween(text_scene, "eiid2", "t2")), 1)
        # The wrong pairings must NOT exist.
        self.assertEqual(len(edgesBetween(text_scene, "eiid1", "t2")), 0)
        self.assertEqual(len(edgesBetween(text_scene, "eiid2", "t1")), 0)

    # ---- Document Creation Time -----------------------------------------

    def testNoDctHasNoOverlay(self):
        _, text_scene = buildScenes(readTml("no_dct.tml"))
        self.assertEqual(text_scene._doc_function_boxes, [])

    def testNoDctScenesStillBuild(self):
        time_scene, text_scene = buildScenes(readTml("no_dct.tml"))
        self.assertIn("eiid1", time_scene.nodes)
        self.assertIn("eiid2", time_scene.nodes)
        self.assertIn("eiid1", text_scene.nodes)
        self.assertIn("eiid2", text_scene.nodes)

    def testDctProducesOverlay(self):
        _, text_scene = buildScenes(readTml("with_dct.tml"))
        self.assertEqual(len(text_scene._doc_function_boxes), 1)

    def testDctDrawnAsInlineNodeWhenInBody(self):
        # A CREATION_TIME TIMEX3 that appears in the text body is rendered
        # as an inline node (in addition to the header overlay). This is the
        # case for E3C documents where the annotators marked an in-body
        # TIMEX3 as DOCTIME (e.g. EN100022, EN100024, EN100466).
        _, text_scene = buildScenes(readTml("with_dct.tml"))
        self.assertIn("t0", text_scene.nodes)

    def testMultipleDocFunctionsInHeader(self):
        # CREATION_TIME and PUBLICATION_TIME both get a header box, in
        # distinct colours, creation time first.
        _, text_scene = buildScenes(readTml("doc_functions.tml"))
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
        _, text_scene = buildScenes(readTml("publication_only.tml"))
        self.assertEqual(len(text_scene._doc_function_boxes), 1)
        self.assertIn("Publication Time", text_scene._doc_function_boxes[0][1])
        self.assertNotIn("t0", text_scene.nodes)

    # ---- Two events linked to each other --------------------------------

    def testTwoLinkedEventsSingleEdgeTimeView(self):
        time_scene, _ = buildScenes(readTml("no_dct.tml"))
        edges = edgesBetween(time_scene, "eiid1", "eiid2")
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].link.rel_type, "BEFORE")

    def testTwoLinkedEventsSingleEdgeTextView(self):
        _, text_scene = buildScenes(readTml("no_dct.tml"))
        edges = edgesBetween(text_scene, "eiid1", "eiid2")
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].link.rel_type, "BEFORE")

    # ---- Link not duplicated --------------------------------------------

    def testSlinkDrawnOnceTimeView(self):
        time_scene, _ = buildScenes(readTml("slink.tml"))
        slinks = [e for e in edgesOf(time_scene) if e.link.link_tag == "SLINK"]
        self.assertEqual(len(slinks), 1, [e.link.get_id_str() for e in slinks])

    def testSlinkDrawnOnceTextView(self):
        _, text_scene = buildScenes(readTml("slink.tml"))
        slinks = [e for e in edgesOf(text_scene) if e.link.link_tag == "SLINK"]
        self.assertEqual(len(slinks), 1, [e.link.get_id_str() for e in slinks])


if __name__ == "__main__":
    unittest.main()
