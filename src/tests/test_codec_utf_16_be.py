import unittest

from id3vx.codec import UTF16BECodec


class CodecUtf16BeTests(unittest.TestCase):
    def test_decodes_string(self):
        """Decodes a string using UTF-16BE encoding"""
        # Arrange
        byte_poop = b'\xd8=\xdc\xa9'
        actual_poop = '💩'

        # System under test
        codec = UTF16BECodec()

        # Act
        decoded_poop = codec.decode(byte_poop)

        # Assert
        self.assertEqual(decoded_poop, actual_poop)
