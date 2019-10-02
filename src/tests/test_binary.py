import unittest

from id3vx.binary import synchsafe, unsynchsafe


class BinaryTest(unittest.TestCase):
    def test_8_bit(self):
        size = 0b01111111
        expected = size

        self.assertEqual(unsynchsafe(size), expected)

    def test_spec_example(self):
        size = 0x0201
        expected = 257

        self.assertEqual(unsynchsafe(size), expected)

    def test_ultra(self):
        self.assertEqual(unsynchsafe(0x7f7f7f7f), 2 ** 28 - 1)

    def test_max(self):
        self.assertEqual(synchsafe(0xFF), 0x17f)
        self.assertEqual(synchsafe(0xFFFF), 0x37f7f)
        self.assertEqual(synchsafe(0xFFFFFF), 0x7_7f_7f_7f)
        self.assertEqual(synchsafe(2 ** 28 - 1), 0x7f_7f_7f_7f)

    def test_roundtrip(self):
        size = 42949672

        encoded = synchsafe(size)
        decoded = unsynchsafe(encoded)

        self.assertEqual(decoded, size)
