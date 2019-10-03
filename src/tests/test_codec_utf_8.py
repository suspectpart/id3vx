import unittest

from id3vx.codec import UTF8Codec


class UTF8CodecTests(unittest.TestCase):
    def test_decodes_string(self):
        """Decodes a string using UTF-8 encoding"""
        # Arrange
        byte_poop = b'\xf0\x9f\x92\xa9'
        actual_poop = '💩'

        # System under test
        codec = UTF8Codec()

        # Act
        decoded_poop = codec.decode(byte_poop)

        # Assert
        self.assertEqual(decoded_poop, actual_poop)

    def test_encodes_string(self):
        """Decodes a string using UTF-8 encoding"""
        # Arrange
        byte_poop = b'\xf0\x9f\x92\xa9\x00'
        actual_poop = '💩'

        # System under test
        codec = UTF8Codec()

        # Act
        encoded_poop = codec.encode(actual_poop)

        # Assert
        self.assertEqual(encoded_poop, byte_poop)
