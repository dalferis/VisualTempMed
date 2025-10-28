"""
Holds the tests for the Event Class.

Written by: asing118
Last Updated by: asing118
"""
import unittest
from pytlex_core.data import Event


class EventTestCase(unittest.TestCase):
    """
    Testing the Constructor.
    """

    def test_null_event_class(self):
        """
        Checks if Test returns an exception after inputting a null for EventClass
        """
        with self.assertRaises(Exception):
            event1 = Event.Event(1, None, "STEM")

    def test_invalid_eid(self):
        """
        Checks if test returns an Error with an invalid eID
        """
        with self.assertRaises(Exception):
            event1 = Event.Event(0, "ASPECTUAL", "STEM")

    def test_invalid_whitespace(self):
        """
        Checks if test returns an error with all whitespace for stem
        """
        with self.assertRaises(Exception):
            event1 = Event.Event(1, "STATE", "")

    def test_invalid_event_class(self):
        """
        Checks if test returns an exception after inputting an invalid class for Event Class
        """
        with self.assertRaises(Exception):
            event1 = Event.Event(1, "Word", "STEM")

    """
    Testing the getters.
    """

    def test_get_stem_trimmed(self):
        """
        Checks the stem is trimmed after getting stem
        """
        event1 = Event.Event(1, "ASPECTUAL", " word word")
        self.assertEqual(event1.stem, "word word")

    def test_stem_none(self):
        """
        Checks that the stem is empty
        """
        event1 = Event.Event(1, "ASPECTUAL", None)
        self.assertEqual(event1.stem, None)

    def test_get_event_class(self):
        """
        Checks that the get Event Class works
        """
        event1 = Event.Event(1, "STATE", "STEM")
        self.assertEqual(event1.event_class, "STATE")

    def test_get_eid(self):
        """
        Checks that correct eID is returned
        """
        event1 = Event.Event(1, "I_STATE", "STEM")
        self.assertEqual(event1.eid, 1)

    def test_get_event_id_str(self):
        """
        Checks that the correct str is returned
        """
        event1 = Event.Event(1, "I_STATE", "STEM")
        self.assertEqual(event1.get_id_str(), "e1")

    def test_to_string_event(self):
        """
        Checks that the to_string returns correct event info
        """
        event1 = Event.Event(1, "ASPECTUAL", "STEM")
        self.assertEqual(event1.to_string(), "EVENT: eid = e1, class = ASPECTUAL, stem = STEM")

    def test_to_json_event(self):
        """
        Checks that the to_json returns correct info
        """
        event1 = Event.Event(1, "OCCURRENCE", "CHECK")
        self.assertEqual(event1.to_json(), "{\"id\":\"e1\", \"eventClass\":\"OCCURRENCE\", \"stem\":\"CHECK\"}")

    """
    Testing Dataclass comparisons
    """

    def test_dataclass_equal(self):
        """
        Checks that the event classes can be equal due to them being dataclasses
        """
        event1 = Event.Event(1, "I_ACTION", "THESTEM")
        event2 = Event.Event(1, "I_ACTION", "THESTEM")
        self.assertEqual(event1, event2)

    def test_dataclass_not_equal_eid(self):
        """
        Checks that the event classes are not equal through stem due to them being dataclasses
        """
        event1 = Event.Event(1, "I_STATE", "STEM")
        event2 = Event.Event(2, "I_STATE", "STEM")
        self.assertNotEqual(event1, event2)

    def test_dataclass_not_equal_event_class(self):
        """
        Checks that the event classes are not equal due to them being dataclasses
        """
        event1 = Event.Event(1, "I_ACTION", "THESTEM")
        event2 = Event.Event(1, "I_STATE", "THESTEM")
        self.assertNotEqual(event1, event2)

    def test_dataclass_not_equal_stem(self):
        """
        Checks that the event classes are not equal through stem due to them being dataclasses
        """
        event1 = Event.Event(1, "I_ACTION", "THESTEM")
        event2 = Event.Event(1, "I_STATE", "STEM")
        self.assertNotEqual(event1, event2)


if __name__ == '__main__':
    unittest.main()
