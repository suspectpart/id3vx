import unittest

from id3vx.codec import UTF16Codec


class CodecUtf16Tests(unittest.TestCase):
    def test_decodes_string(self):
        """Decodes a string using UTF-16 encoding"""
        # Arrange
        byte_poop_with_bom = b'\xff\xfe=\xd8\xa9\xdc'
        actual_poop = '💩'

        # System under test
        codec = UTF16Codec()

        # Act
        decoded_poop = codec.decode(byte_poop_with_bom)

        # Assert
        self.assertEqual(decoded_poop, actual_poop)
