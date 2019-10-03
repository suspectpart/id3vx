import unittest

from id3vx.binary import synchsafe, unsynchsafe


class BinaryTest(unittest.TestCase):
    def test_unsynchsafe_small_int(self):
        size = 0b01111111

        self.assertEqual(unsynchsafe(size), size)

    def test_unsynchsafe_example_from_specification(self):
        size = 0x0201
        expected = 257

        self.assertEqual(unsynchsafe(size), expected)

    def test_unsynchsafe_highest_possible_int(self):
        self.assertEqual(unsynchsafe(0x7f7f7f7f), 2 ** 28 - 1)

    def test_synchsafe_at_boundaries(self):
        self.assertEqual(synchsafe(0xFF), 0x17f)
        self.assertEqual(synchsafe(0xFFFF), 0x37f7f)
        self.assertEqual(synchsafe(0xFFFFFF), 0x7_7f_7f_7f)
        self.assertEqual(synchsafe(2 ** 28 - 1), 0x7f_7f_7f_7f)

    def test_synchsafe_then_unsynchsafe_low(self):
        size = 2 ** 6

        encoded = synchsafe(size)
        decoded = unsynchsafe(encoded)

        self.assertEqual(decoded, size)

    def test_synchsafe_then_unsynchsafe_high(self):
        size = 42949672

        encoded = synchsafe(size)
        decoded = unsynchsafe(encoded)

        self.assertEqual(decoded, size)

    def test_synchsafe_then_unsynchsafe_zero(self):
        size = 0

        encoded = synchsafe(size)
        decoded = unsynchsafe(encoded)

        self.assertEqual(decoded, size)
