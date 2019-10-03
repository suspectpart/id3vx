import unittest

from id3vx.codec import Latin1Codec


class CodecLatin1Tests(unittest.TestCase):
    def test_decodes_string(self):
        """Decodes a string using Latin1 encoding"""
        # Arrange
        latin1_byte_string = b'abc'
        expected_string = 'abc'

        # System under test
        codec = Latin1Codec()

        # Act
        string = codec.decode(latin1_byte_string)

        # Assert
        self.assertEqual(string, expected_string)
