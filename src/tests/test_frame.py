import unittest
from io import BytesIO

from id3vx.frame import FrameHeader, Frame, TextFrame


class FrameHeaderTests(unittest.TestCase):
    def test_reads_header_from_stream(self):
        """Reads FrameHeader from a bytes stream"""
        # Arrange
        frame_id = b'PRIV'
        size = b'\x00\x00\x00\xFF'
        flags = b'\x00\x00'

        stream = BytesIO(frame_id + size + flags)

        # Act
        header = FrameHeader.read_from(stream)

        # Assert
        self.assertEqual(header.frame_size(), 255)
        self.assertEqual(header.flags(), FrameHeader.Flags(0))
        self.assertEqual(header.id(), frame_id)

    def test_reads_all_flags(self):
        """Reads all flags correctly"""
        # Arrange
        frame_id = b'PRIV'
        size = b'\x00\x00\x00\xFF'
        flags = 0b1110000011100000.to_bytes(2, "big")

        stream = BytesIO(frame_id + size + flags)

        # Act
        header = FrameHeader.read_from(stream)

        # Assert
        self.assertIn(FrameHeader.Flags.Compression, header.flags())
        self.assertIn(FrameHeader.Flags.Encryption, header.flags())
        self.assertIn(FrameHeader.Flags.FileAlterPreservation, header.flags())
        self.assertIn(FrameHeader.Flags.GroupingIdentity, header.flags())
        self.assertIn(FrameHeader.Flags.ReadOnly, header.flags())
        self.assertIn(FrameHeader.Flags.TagAlterPreservation, header.flags())

    def test_reads_some_flags(self):
        """Reads some flags correctly"""
        # Arrange
        frame_id = b'PRIV'
        size = b'\x00\x00\x00\xFF'
        flags = 0b0000000011100000.to_bytes(2, "big")

        stream = BytesIO(frame_id + size + flags)

        # Act
        header = FrameHeader.read_from(stream)

        # Assert
        self.assertIn(FrameHeader.Flags.Compression, header.flags())
        self.assertIn(FrameHeader.Flags.Encryption, header.flags())
        self.assertIn(FrameHeader.Flags.GroupingIdentity, header.flags())

    def test_reads_header_if_size_bigger_than_zero(self):
        """Reads FrameHeader as long as size is present"""
        # Arrange
        frame_id = b'\x00\x00\x00\x00'
        frame_size = b'\x00\x00\x00\x01'
        flags = b'\x00\x00'

        stream = BytesIO(frame_id + frame_size + flags)

        # Act
        header = FrameHeader.read_from(stream)

        # Assert
        self.assertEqual(header.frame_size(), 1)
        self.assertEqual(header.id(), frame_id)
        self.assertEqual(header.flags(), FrameHeader.Flags(0))

    def test_no_header_from_too_short_stream(self):
        """Fails to read FrameHeader from a too short byte stream"""
        # Arrange
        frame_id = b'PRIV'
        size = b'\x00\x00\x00\xFF'

        stream = BytesIO(frame_id + size)

        # Act
        header = FrameHeader.read_from(stream)

        # Assert
        self.assertIsNone(header)

    def test_reads_no_header_if_size_is_zero(self):
        """Fails to read FrameHeader if size is zero"""
        # Arrange
        frame_id = b'PRIV'
        size = b'\x00\x00\x00\x00'
        flags = b'\x00\x00'

        stream = BytesIO(frame_id + size + flags)

        # Act
        header = FrameHeader.read_from(stream)

        # Assert
        self.assertIsNone(header)

    def test_converts_back_to_bytes(self):
        # Arrange
        frame_id = b'PRIV'
        size = 3333
        flags = 0b1100_0000_0000_0000

        expected_bytes = b'PRIV\x00\x00\r\x05\xc0\x00'

        # System under test
        header = FrameHeader(frame_id, size, flags)

        # Act
        header_bytes = bytes(header)

        # Assert
        self.assertEqual(header_bytes, expected_bytes)


class FrameTests(unittest.TestCase):
    def test_represents_every_frame_id(self):
        """Represents every Frame ID"""
        # Arrange - Act - Assert
        self.assertTrue(Frame.represents(b'TXXX'))
        self.assertTrue(Frame.represents(b'TALB'))
        self.assertTrue(Frame.represents(b'WXXX'))
        self.assertTrue(Frame.represents(b'WOAR'))
        self.assertTrue(Frame.represents(b'COMM'))
        self.assertTrue(Frame.represents(b'PRIV'))
        self.assertTrue(Frame.represents(b'????'))

    def test_exposes_fields(self):
        """Exposes relevant fields"""
        # Arrange
        header = FrameHeader(b'PRIV', 100, 0)
        fields = b'\x0a\x0f\x00\x0f\x0c'

        # System under test
        frame = Frame(header, fields)

        # Assert
        self.assertEqual(frame.header(), header)
        self.assertEqual(frame.id(), "PRIV")
        self.assertEqual(frame.fields(), fields)
        self.assertEqual(str(frame), str(fields))
        self.assertEqual(frame.name(), "Private frame")

    def test_serializes_to_bytes(self):
        """Serializes itself to bytes"""
        # Arrange
        header = FrameHeader(b'PRIV', 100, 0)
        header_bytes = bytes(header)
        fields = b'\x0a\x0f\x00\x0f\x0c'

        # System under test
        frame = Frame(header, fields)

        # Act
        byte_string = bytes(frame)

        # Assert
        self.assertEqual(byte_string, header_bytes + fields)

    def test_defaults_name_to_identifier(self):
        """Defaults to Frame ID if name is unknown"""
        # Arrange
        header = FrameHeader(b'ABCD', 100, 0)
        fields = b'\x0a\x0f\x00\x0f\x0c'

        # System under test
        frame = Frame(header, fields)

        # Act - Assert
        self.assertEqual(frame.name(), "ABCD")

    def test_no_frame_if_header_invalid(self):
        """Defaults to Frame ID if name is unknown"""
        # Arrange
        broken_header = bytes(10)
        fields = bytes(100)

        stream = BytesIO(broken_header + fields)

        # System under test
        frame = Frame.read_from(stream)

        # Act - Assert
        self.assertIsNone(frame)

    def test_read_frame_from_stream(self):
        """Defaults to Frame ID if name is unknown"""
        # Arrange
        fields = b'\x00Album'
        size = len(fields)
        header = FrameHeader(b'TALB', size, 0)
        frame = TextFrame(header, fields)

        stream = BytesIO(bytes(frame))

        # System under test
        frame = Frame.read_from(stream)

        # Act - Assert
        self.assertEqual(type(frame), TextFrame)
        self.assertEqual(frame.id(), "TALB")
        self.assertEqual(frame.text(), "Album")
