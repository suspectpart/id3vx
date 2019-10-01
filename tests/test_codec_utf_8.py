import unittest

from codec import UTF8Codec


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

    def test_split_empty_string(self):
        """Splits an empty string to an empty string"""
        # Arrange
        byte_string = b''

        # System under test
        codec = UTF8Codec()

        # Act
        parts = list(codec.split_decode(byte_string))

        # Assert
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], '')

    def test_split_single_separator(self):
        """Splits a string containing a single null-separator"""
        # Arrange
        byte_string = b'\x00'

        # System under test
        codec = UTF8Codec()

        # Act
        parts = list(codec.split_decode(byte_string))

        # Assert
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], '')

    def test_splits_two_separators(self):
        """Splits a string containing two empty null-separators"""
        # Arrange
        byte_string = b'\x00\x00'

        # System under test
        codec = UTF8Codec()

        # Act
        parts = list(codec.split_decode(byte_string))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], '')
        self.assertEqual(parts[1], '')

    def test_split_single_token(self):
        """Splits a string containing a single null-terminated token"""
        # Arrange
        byte_string = b'a\x00'

        # System under test
        codec = UTF8Codec()

        # Act
        parts = list(codec.split_decode(byte_string))

        # Assert
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], 'a')

    def test_split_two_tokens(self):
        """Splits a string containing two null-terminated tokens"""
        # Arrange
        byte_string = b'a\x00b\x00'

        # System under test
        codec = UTF8Codec()

        # Act
        parts = list(codec.split_decode(byte_string))

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
        codec = UTF8Codec()

        # Act
        parts = list(codec.split_decode(byte_string))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], special_char)
        self.assertEqual(parts[1], special_char)

    def test_splits_tokens_with_maxsplit(self):
        """Splits a string maxsplit times"""
        # Arrange
        byte_string = b'a\x00b\x00\x00\x00x0a\xcf\xca'

        # System under test
        codec = UTF8Codec()

        # Act
        parts = list(codec.split(byte_string, 1))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], b'a')
        self.assertEqual(parts[1], b'b\x00\x00\x00x0a\xcf\xca')
