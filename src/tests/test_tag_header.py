import unittest
from io import BytesIO

from id3vx.binary import unsynchsafe
from id3vx.tag import TagHeader, NoTagError, UnsupportedError


class TagHeaderTest(unittest.TestCase):
    def test_raises_on_wrong_identifier(self):
        """Fails to initialize on wrong identifier"""
        # Arrange
        wrong_identifier = '???'

        # Act - Assert
        with self.assertRaises(NoTagError):
            TagHeader(wrong_identifier, 0, 0, TagHeader.Flags(0), 0)

    def test_raises_on_unsynchronization_tags(self):
        """Rejects tags using unsychronization"""
        # Arrange
        flags = TagHeader.Flags.Sync

        # Act - Assert
        with self.assertRaises(UnsupportedError):
            TagHeader('ID3', 3, 0, flags, 0)

    def test_raises_on_unsupported_version(self):
        """Fails to initialize on unsupported version"""
        # Arrange
        wrong_identifier = 'ID3'
        unsupported_version = 2
        flags = TagHeader.Flags(0)

        # Act - Assert
        with self.assertRaises(UnsupportedError):
            TagHeader(wrong_identifier, unsupported_version, 0, flags, 0)

    def test_exposes_fields(self):
        """Exposes all relevant fields"""
        # Arrange
        identifier = 'ID3'
        major, minor = (3, 0)
        flags = TagHeader.Flags.Experimental
        tag_size = 1000

        # System under test
        header = TagHeader(identifier, major, minor, flags, tag_size)

        # Assert
        self.assertEqual(len(header), 10)
        self.assertEqual(header.tag_size, 1000)
        self.assertEqual(header.major, major)
        self.assertEqual(header.minor, minor)
        self.assertEqual(header.flags, flags)

    def test_deserializes(self):
        """Deserializes from bytes"""
        # Arrange
        f = TagHeader.Flags  # for brevity's sake
        byte_string = b'ID3\x03\x01\x60\x00\x00\x0A\x0A'

        flags = f.Experimental | f.Extended
        major = 3
        minor = 1
        expected_tag_size = unsynchsafe(0x0A0A)

        # System under test / Act
        header = TagHeader.read(BytesIO(byte_string))

        # Assert
        self.assertEqual(len(header), 10)
        self.assertEqual(header.tag_size, expected_tag_size)
        self.assertEqual(header.major, major)
        self.assertEqual(header.minor, minor)
        self.assertEqual(header.flags, flags)
        self.assertEqual(bytes(header), byte_string)

    def test_serialization(self):
        """Deserializes from bytes and serializes back to bytes"""
        # Arrange
        byte_string = b'ID3\x03\x01\x60\x00\x00\x00\x0A'

        # System under test / Act
        header = TagHeader.read(BytesIO(byte_string))

        # Act
        serialized = bytes(header)

        # Assert
        self.assertEqual(serialized, byte_string)
