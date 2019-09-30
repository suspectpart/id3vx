import unittest

from codec import Codec, _CODECS


class CodecTests(unittest.TestCase):
    def test_disallowed(self):
        self.assertEqual(Codec.default(), _CODECS.get(0))
