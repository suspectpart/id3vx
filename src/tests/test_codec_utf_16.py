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
        byte_string = b'\xff\xfe\x00\x00'

        # System under test
        codec = UTF16Codec()

        # Act
        parts = list(codec.split_decode(byte_string, 1))

        # Assert
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], '')

    def test_splits_two_separators(self):
        """Splits a string containing two empty null-separators"""
        # Arrange
        byte_string = b'\xff\xfe\x00\x00\xfe\xff\x00\x00'

        # System under test
        codec = UTF16Codec()

        # Act
        parts = list(codec.split_decode(byte_string, 2))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], '')
        self.assertEqual(parts[1], '')

    def test_split_single_token(self):
        """Splits a string containing a single null-terminated token"""
        # Arrange
        byte_string = b'\xff\xfea\x00\x00\x00'

        # System under test
        codec = UTF16Codec()

        # Act
        parts = list(codec.split_decode(byte_string, 1))

        # Assert
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], 'a')

    def test_split_two_tokens_no_bom(self):
        """Splits and decodes a UTF-16LE encoded string without BOM"""
        # Arrange
        le_byte_string = b'a\x00\x00\x00b\x00\x00\x00'

        # System under test
        codec = UTF16Codec()

        # Act
        parts = list(codec.split_decode(le_byte_string, 2))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], 'a')
        self.assertEqual(parts[1], 'b')

    def test_fails_with_no_bom_and_be(self):
        """Fails to split and decode a UTF-16BE encoded string without BOM"""
        # Arrange
        be_byte_string = b'\x00a\x00\x00\x00b\x00\x00'

        # System under test
        codec = UTF16Codec()

        # Act
        with self.assertRaises(UnicodeDecodeError):
            list(codec.split_decode(be_byte_string))

    def test_split_two_tokens_with_le_bom(self):
        """Splits a string with UTF-16LE encoded tokens"""
        # Arrange
        byte_string = b'\xff\xfea\x00\x00\x00b\x00\x00\x00'

        # System under test
        codec = UTF16Codec()

        # Act
        parts = list(codec.split_decode(byte_string, 2))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], 'a')
        self.assertEqual(parts[1], 'b')

    def test_split_two_tokens_with_be_bom(self):
        """Splits a string with UTF-16BE encoded tokens"""
        # Arrange
        byte_string = b'\xfe\xff\x00a\x00\x00\xfe\xff\x00b\x00\x00'

        # System under test
        codec = UTF16Codec()

        # Act
        parts = list(codec.split_decode(byte_string, 2))

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
        parts = list(codec.split_decode(byte_string, 2))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], 'a')
        self.assertEqual(parts[1], 'b')

    def test_splits_tokens_with_maxsplit(self):
        """Splits a string maxsplit times"""
        # Arrange
        byte_string = b'a\x00\x00\x00b\x00\x00\x00\x0a\xcf\xca'

        # System under test
        codec = UTF16Codec()

        # Act
        parts = list(codec.split(byte_string, 1))

        # Assert
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], b'a\x00')
        self.assertEqual(parts[1], b'b\x00\x00\x00\x0a\xcf\xca')
