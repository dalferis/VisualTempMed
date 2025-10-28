# Written by: jsegr004
# Last updated: jsegr004
import unittest
from pytlex_core.data.TimeX import TimeX


class TimeXTestCase(unittest.TestCase):

    def test_default(self):
        timex0 = TimeX(0, 'value', True, 'phrase')  # Only default values
        self.assertEqual(timex0.tID, 0)
        self.assertEqual(timex0.value, 'value')
        self.assertEqual(timex0.temporalFunction, True)
        self.assertEqual(timex0.phrase, 'phrase')

    def test_getters(self):
        timex1 = TimeX(0, 'value', True, 'phrase', 'SET', 'AFTER', 'CREATION_TIME', 0, 'quant', 'freq', 1,
                       2)  # All values
        self.assertEqual(timex1.get_id_str(), 't0')
        self.assertEqual(timex1.get_anchor_id_str(), 't0')
        self.assertEqual(timex1.get_begin_point_str(), 't1')
        self.assertEqual(timex1.get_end_point_str(), 't2')

    def test_type(self):
        timex2 = TimeX(0, 'value', True, 'phrase', type='DATE')  # Change type, with valid option
        self.assertEqual(timex2.type, 'DATE')

        with self.assertRaises(Exception):
            TimeX(0, 'value', True, 'phrase', type='type')  # Change type, with invalid option

    def test_mod(self):
        timex3 = TimeX(0, 'value', True, 'phrase', mod='AFTER')  # Change mod, with valid option
        self.assertEqual(timex3.mod, 'AFTER')

        with self.assertRaises(Exception):
            TimeX(0, 'value', True, 'phrase', mod='mod')  # Change mod, with invalid option

    def test_documentFunction(self):
        timex4 = TimeX(0, 'value', True, 'phrase', documentFunction='CREATION_TIME')  # Change doc Func, valid option
        self.assertEqual(timex4.documentFunction, 'CREATION_TIME')

        with self.assertRaises(Exception):
            TimeX(0, 'value', True, 'phrase', documentFunction='docFunc')  # Change doc Func, invalid option

    def test_anchorID(self):
        timex5 = TimeX(0, 'value', True, 'phrase', anchorID=0)  # Change anchor id, with valid option
        self.assertEqual(timex5.anchorID, 0)

        with self.assertRaises(Exception):
            TimeX(0, 'value', True, 'phrase', anchorID=-1)  # Change anchor id, with invalid option

    def test_quant_and_freq(self):
        timex6 = TimeX(0, 'value', True, 'phrase', quant='quant', freq='freq')  # Change quant and freq, valid
        self.assertEqual(timex6.quant, 'quant')
        self.assertEqual(timex6.freq, 'freq')

        # with self.assertRaises(Exception):
        #     TimeX(0, 'value', True, 'phrase', type='SET')  # Error: quant or freq can't be None if type is SET

    def test_beginPoint_and_endPoint(self):
        timex7 = TimeX(0, 'value', True, 'phrase', beginPoint=1, endPoint=2)  # Change beginPoint and endPoint, valid
        self.assertEqual(timex7.beginPoint, 1)
        self.assertEqual(timex7.endPoint, 2)

        with self.assertRaises(Exception):
            TimeX(0, 'value', True, 'phrase', beginPoint=-1)
        with self.assertRaises(Exception):
            TimeX(0, 'value', True, 'phrase', endPoint=-2)


if __name__ == "__main__":
    unittest.main()