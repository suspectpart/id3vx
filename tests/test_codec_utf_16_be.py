import unittest

from codec import UTF16BECodec


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

    def test_split_empty_string(self):
        """Splits an empty string to an empty string"""
        # Arrange
        byte_string = b''

        # System under test
        codec = UTF16BECodec()

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
        codec = UTF16BECodec()

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
        codec = UTF16BECodec()

        # Act
        parts = list(codec.split_decode(byte_string))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], '')
        self.assertEqual(parts[1], '')

    def test_split_single_token(self):
        """Splits a string containing a single null-terminated token"""
        # Arrange
        byte_string = b'\x00a\x00\x00'

        # System under test
        codec = UTF16BECodec()

        # Act
        parts = list(codec.split_decode(byte_string))

        # Assert
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], 'a')

    def test_split_two_tokens(self):
        """Splits a string containing two null-terminated tokens"""
        # Arrange
        byte_string = b'\x00a\x00\x00\x00b\x00\x00'

        # System under test
        codec = UTF16BECodec()

        # Act
        parts = list(codec.split_decode(byte_string))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], 'a')
        self.assertEqual(parts[1], 'b')

    def test_split_two_tokens_omitted_terminator(self):
        """Splits a string containing two null-terminated tokens"""
        # Arrange
        byte_string = b'\x00a\x00\x00\x00b'

        # System under test
        codec = UTF16BECodec()

        # Act
        parts = list(codec.split_decode(byte_string))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], 'a')
        self.assertEqual(parts[1], 'b')

    def test_splits_tokens_with_maxsplit(self):
        """Splits a string maxsplit times"""
        # Arrange
        byte_string = b'\x00a\x00\x00\x00b\x00\x00\x0a\xcf\xca'

        # System under test
        codec = UTF16BECodec()

        # Act
        parts = list(codec.split(byte_string, 1))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], b'\x00a')
        self.assertEqual(parts[1], b'\x00b\x00\x00\x0a\xcf\xca')
