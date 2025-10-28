# Written by: kfont015
# Last updated: gparr014

import unittest
from pytlex_core.data import Signal


# updated the unit tests to remove the standalone 'assert' keyword
# as it is no longer a standard due to self.assertX being able to accumulate the output
# gparr014


class SignalTestCase(unittest.TestCase):
    """
        Testing constructor for absurd input
    """
    def test_null_signal_class(self):
        with self.assertRaises(Exception):
            Signal.Event(None, None)

    def test_invalid_signal_id(self):
        with self.assertRaises(Exception):
            Signal.Event(0, "Valid string")

    def test_invalid_signal_string(self):
        with self.assertRaises(Exception):
            Signal.Event(2, "")

    """
        Testing the getters and setters
    """
    def test_signal_id_getter(self):
        signal = Signal.Signal(1, "SignalValid")
        self.assertEqual(signal.signal_id, 1)

    def test_signal_string_getter(self):
        signal = Signal.Signal(1, "SignalValid")
        self.assertEqual(signal.signal_string, "SignalValid")

    def test_signal_id_setter(self):
        signal = Signal.Signal(1, "SignalValid")
        signal.signal_id = 5
        self.assertEqual(signal.signal_id, 5)

    def test_signal_string_setter(self):
        signal = Signal.Signal(1, "SignalValid")
        signal.signal_string = "HelloWorld"
        self.assertEqual(signal.signal_string, "HelloWorld")

    """
       Test custom methods
    """
    def test_get_id_str(self):
        signal = Signal.Signal(1, "testString")
        self.assertEqual(signal.get_id_str(), "sid1")

    def test_to_json(self):
        test_value = "{\"id\": \"sid1\", \"signalString\": \"testString\"}"
        signal = Signal.Signal(1, "testString")
        self.assertEqual(signal.to_json(), test_value)

    def test__str__(self):
        test_value = "Signal: {id = 1, String = testString}"
        signal = Signal.Signal(1, "testString")
        self.assertEqual(str(signal), test_value)

    """
       Test object comparison
    """
    def test_signal_object_equal(self):
        signal1 = Signal.Signal(1, "TEST_1")
        signal2 = Signal.Signal(1, "TEST_1")
        self.assertEqual(signal1, signal2)

    def test_signal_id_object_not_equal(self):
        signal1 = Signal.Signal(1, "TEST_1").signal_id
        signal2 = Signal.Signal(2, "TEST_1").signal_id
        self.assertNotEqual(signal1, signal2)

    def test_signal_string_object_not_equal(self):
        signal1 = Signal.Signal(1, "TEST_1")
        signal2 = Signal.Signal(1, "TEST_2")
        self.assertNotEqual(signal1.signal_string, signal2.signal_string)


if __name__ == '__main__':
    unittest.main()
