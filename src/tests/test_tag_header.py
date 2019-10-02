import unittest
from io import BytesIO

from id3vx.tag import TagHeader


class TagHeaderTest(unittest.TestCase):
    def test_raises_on_wrong_identifier(self):
        """Fails to initialize on wrong identifier"""
        # Arrange
        wrong_identifier = b'???'

        # Act - Assert
        with self.assertRaises(ValueError):
            TagHeader(wrong_identifier, 0, 0, 0, 0)

    def test_exposes_fields(self):
        """Exposes all relevant fields"""
        # Arrange
        identifier = b'ID3'
        major, minor = (3, 0)
        flags = TagHeader.Flags.Experimental
        tag_size = 1000

        # System under test
        header = TagHeader(identifier, major, minor, flags, tag_size)

        # Assert
        self.assertEqual(len(header), 10)
        self.assertEqual(header.tag_size(), 1010)
        self.assertEqual(header.version(), (major, minor))
        self.assertEqual(header.flags(), flags)

    def test_deserializes(self):
        """Deserializes from bytes"""
        # Arrange
        f = TagHeader.Flags  # for brevity's sake
        byte_string = b'ID3\x03\x01\xe0\x00\x00\x0A\x0A'

        flags = f.Experimental | f.Extended | f.Sync
        version = (3, 1)
        tag_size = 0x0A0A + 10

        # System under test / Act
        header = TagHeader.read_from(BytesIO(byte_string))

        # Assert
        self.assertEqual(len(header), 10)
        self.assertEqual(header.tag_size(), tag_size)
        self.assertEqual(header.version(), version)
        self.assertEqual(header.flags(), flags)
        self.assertEqual(bytes(header), byte_string)

    def test_serialization(self):
        """Deserializes from bytes and serializes back to bytes"""
        # Arrange
        byte_string = b'ID3\x03\x01\xe0\x00\x00\x0A\x0A'

        # System under test / Act
        header = TagHeader.read_from(BytesIO(byte_string))

        # Act
        serialized = bytes(header)

        # Assert
        self.assertEqual(serialized, byte_string)