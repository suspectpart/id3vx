import unittest

from src.codec import Codec, Latin1Codec, UTF16Codec, UTF16BECodec, UTF8Codec


class CodecTests(unittest.TestCase):
    def test_default(self):
        """Codec defaults to Latin1 / ISO 8859-1"""
        self.assertEqual(Codec.default(), Latin1Codec())

    def test_get_by_magic_number(self):
        """Codec can be retrieved by magic id3v2.3 encoding number"""
        self.assertEqual(Codec.get(0), Latin1Codec())
        self.assertEqual(Codec.get(1), UTF16Codec())
        self.assertEqual(Codec.get(2), UTF16BECodec())
        self.assertEqual(Codec.get(3), UTF8Codec())
