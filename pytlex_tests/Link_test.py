# Written by: jsegr004
# Last updated: gparr014 - added tests for methods

import unittest
from pytlex_core.data.TimeX import TimeX
from pytlex_core.data.Link import Link
from pytlex_core.data.Instance import Instance
from pytlex_core.data.Event import Event
from pytlex_core.data.Signal import Signal

# Valid test inputs
timex0 = TimeX(1, 'value0', True, 'phrase0')
timex1 = TimeX(2, 'value1', True, 'phrase1')

event0 = Event(1, "I_STATE", "STEM")
event1 = Event(2, "I_STATE", "STEM")

instance0 = Instance(1, event0.get_id_str(), event0.event_class, "PAST", "PERFECTIVE", "ADJECTIVE", "POS")
instance1 = Instance(2, event1.get_id_str(), event1.event_class,"PRESENT", "PROGRESSIVE", "VERB", "NEG")

signal = Signal(1, 'signal')


class LinkTestCases(unittest.TestCase):
    def test_default(self):
        link0 = Link(0, 'ALINK', 'INITIATES', timex0.get_id_str(), timex1.get_id_str())
        link1 = Link(1, 'ALINK', 'INITIATES', instance0.get_id_str(), instance1.get_id_str())
        self.assertEqual(link0.link_id, 0)
        self.assertEqual(link0.link_tag, 'ALINK')
        self.assertEqual(link0.rel_type, 'INITIATES')
        self.assertTrue(isinstance(link0.start_node, str))
        self.assertTrue(isinstance(link0.related_to_node, str))
        self.assertTrue(isinstance(link1.start_node, str))
        self.assertTrue(isinstance(link1.related_to_node, str))

    def test_non_default(self):
        link2 = Link(0, 'ALINK', 'INITIATES', timex0.get_id_str(), timex1.get_id_str(), signal.get_id_str(), 'USER', 'syntax')
        self.assertEqual(link2.signal, signal.get_id_str())
        self.assertEqual(link2.origin_type, 'USER')
        self.assertEqual(link2.syntax, 'syntax')

    def test_exceptions(self):
        with self.assertRaises(Exception):  # Link ID is less than 0
            Link(-1, 'ALINK', 'INITIATES', timex0.get_id_str(), timex1.get_id_str())

        with self.assertRaises(Exception):  # Link Tag is invalid
            Link(0, 'LINK', 'INITIATES', timex0.get_id_str(), timex1.get_id_str())

        with self.assertRaises(Exception):  # start_node cannot be none
            Link(0, 'ALINK', 'INITIATES', None, timex1.get_id_str())

        with self.assertRaises(Exception):  # related_to_node cannot be none
            Link(0, 'ALINK', 'INITIATES', timex0.get_id_str(), None)

        with self.assertRaises(Exception):  # start_node cannot be Event
            Link(0, 'ALINK', 'INITIATES', event0.get_id_str(), timex1.get_id_str())

        with self.assertRaises(Exception):  # related_to_node cannot be Event
            Link(0, 'ALINK', 'INITIATES', timex0.get_id_str(), event1.get_id_str())

    def test_invalid_link_tags(self):
        with self.assertRaises(Exception):  # origin_type is invalid
            Link(0, 'TLINK', 'BEFORE', timex0.get_id_str(), timex1.get_id_str(), origin_type='Invalid')

        with self.assertRaises(Exception):  # wrong tlink type
            Link(0, 'ALINK', 'BEFORE', timex0.get_id_str(), timex1.get_id_str())

        with self.assertRaises(Exception):  # wrong tlink type
            Link(0, 'SLINK', 'INITIATES', timex0.get_id_str(), timex1.get_id_str())

        with self.assertRaises(Exception):  # wrong tlink type
            Link(0, 'TLINK', 'INITIATES', timex0.get_id_str(), timex1.get_id_str())

    # test __hash__(self)
    # -> correct hash
    def test___hash__(self):
        valid = Link(10, 'ALINK', 'INITIATES', timex0.get_id_str(), timex1.get_id_str())

        # assert correct hash
        self.assertEqual(valid.__hash__(), hash(str(valid.link_id) + valid.link_tag + valid.start_node + valid.related_to_node))

    # test to_json(self)
    def test_to_json(self):
        valid = Link(10, 'ALINK', 'INITIATES', timex0.get_id_str(), timex1.get_id_str(), signal.get_id_str())

        print(valid.to_json())


if __name__ == '__main__':
    unittest.main()
