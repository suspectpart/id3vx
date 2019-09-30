import unittest

from codec import Codec


class CodecLatin1Tests(unittest.TestCase):
    latin_1 = 0

    def test_split_empty_string(self):
        """Splits an empty string to an empty string"""
        # Arrange
        byte_string = b''

        # System under test
        codec = Codec(self.latin_1)

        # Act
        parts = list(codec.split(byte_string))

        # Assert
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], '')

    def test_split_single_separator(self):
        """Splits a string containing a single null-separator"""
        # Arrange
        byte_string = b'\x00'

        # System under test
        codec = Codec(self.latin_1)

        # Act
        parts = list(codec.split(byte_string))

        # Assert
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], '')

    def test_splits_two_separators(self):
        """Splits a string containing two empty null-separators"""
        # Arrange
        byte_string = b'\x00\x00'

        # System under test
        codec = Codec(self.latin_1)

        # Act
        parts = list(codec.split(byte_string))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], '')
        self.assertEqual(parts[1], '')

    def test_split_single_token(self):
        """Splits a string containing a single null-terminated token"""
        # Arrange
        byte_string = b'a\x00'

        # System under test
        codec = Codec(self.latin_1)

        # Act
        parts = list(codec.split(byte_string))

        # Assert
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], 'a')

    def test_split_two_tokens(self):
        """Splits a string containing two null-terminated tokens"""
        # Arrange
        byte_string = b'a\x00b\x00'

        # System under test
        codec = Codec(self.latin_1)

        # Act
        parts = list(codec.split(byte_string))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], 'a')
        self.assertEqual(parts[1], 'b')

    def test_split_two_tokens_omitted_terminator(self):
        """Splits a string containing a non null-terminated last token"""
        # Arrange
        byte_string = b'a\x00b'

        # System under test
        codec = Codec(self.latin_1)

        # Act
        parts = list(codec.split(byte_string))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], 'a')
        self.assertEqual(parts[1], 'b')


class CodecUtf8Tests(unittest.TestCase):
    utf_8 = 3

    def test_split_empty_string(self):
        """Splits an empty string to an empty string"""
        # Arrange
        byte_string = b''

        # System under test
        codec = Codec(self.utf_8)

        # Act
        parts = list(codec.split(byte_string))

        # Assert
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], '')

    def test_split_single_separator(self):
        """Splits a string containing a single null-separator"""
        # Arrange
        byte_string = b'\x00'

        # System under test
        codec = Codec(self.utf_8)

        # Act
        parts = list(codec.split(byte_string))

        # Assert
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], '')

    def test_splits_two_separators(self):
        """Splits a string containing two empty null-separators"""
        # Arrange
        byte_string = b'\x00\x00'

        # System under test
        codec = Codec(self.utf_8)

        # Act
        parts = list(codec.split(byte_string))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], '')
        self.assertEqual(parts[1], '')

    def test_split_single_token(self):
        """Splits a string containing a single null-terminated token"""
        # Arrange
        byte_string = b'a\x00'

        # System under test
        codec = Codec(self.utf_8)

        # Act
        parts = list(codec.split(byte_string))

        # Assert
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], 'a')

    def test_split_two_tokens(self):
        """Splits a string containing two null-terminated tokens"""
        # Arrange
        byte_string = b'a\x00b\x00'

        # System under test
        codec = Codec(self.utf_8)

        # Act
        parts = list(codec.split(byte_string))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], 'a')
        self.assertEqual(parts[1], 'b')

    def test_split_two_tokens_unicode(self):
        """Splits a string containing two null-terminated tokens"""
        # Arrange
        special_char = "Ͻ"
        encoded = special_char.encode("utf-8")
        byte_string = encoded + b'\x00' + encoded + b'\x00'

        # System under test
        codec = Codec(self.utf_8)

        # Act
        parts = list(codec.split(byte_string))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], special_char)
        self.assertEqual(parts[1], special_char)
