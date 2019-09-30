import unittest

from codec import UTF16Codec


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

    def test_split_empty_string(self):
        """Splits an empty string to an empty string"""
        # Arrange
        byte_string = b''

        # System under test
        codec = UTF16Codec()

        # Act
        parts = list(codec.split_decode(byte_string))

        # Assert
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], '')

    def test_split_single_separator(self):
        """Splits a string containing a single null-separator"""
        # Arrange
        byte_string = b'\x00\x00'

        # System under test
        codec = UTF16Codec()

        # Act
        parts = list(codec.split_decode(byte_string))

        # Assert
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], '')

    def test_splits_two_separators(self):
        """Splits a string containing two empty null-separators"""
        # Arrange
        byte_string = b'\x00\x00\x00\x00'

        # System under test
        codec = UTF16Codec()

        # Act
        parts = list(codec.split_decode(byte_string))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], '')
        self.assertEqual(parts[1], '')

    def test_split_single_token(self):
        """Splits a string containing a single null-terminated token"""
        # Arrange
        byte_string = b'a\x00\x00\x00'

        # System under test
        codec = UTF16Codec()

        # Act
        parts = list(codec.split_decode(byte_string))

        # Assert
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], 'a')

    def test_split_two_tokens(self):
        """Splits a string containing two null-terminated tokens"""
        # Arrange
        byte_string = b'a\x00\x00\x00b\x00\x00\x00'

        # System under test
        codec = UTF16Codec()

        # Act
        parts = list(codec.split_decode(byte_string))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], 'a')
        self.assertEqual(parts[1], 'b')

    def test_split_two_tokens_omitted_terminator(self):
        """Splits a string containing two null-terminated tokens"""
        # Arrange
        byte_string = b'a\x00\x00\x00b\x00'

        # System under test
        codec = UTF16Codec()

        # Act
        parts = list(codec.split_decode(byte_string))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], 'a')
        self.assertEqual(parts[1], 'b')
