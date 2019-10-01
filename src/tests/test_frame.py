import unittest
from io import BytesIO

from id3vx.frame import FrameHeader


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
        self.assertEqual(header.size(), 255)
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
        size = b'\x00\x00\x00\x01'
        flags = b'\x00\x00'

        stream = BytesIO(frame_id + size + flags)

        # Act
        header = FrameHeader.read_from(stream)

        # Assert
        self.assertEqual(header.size(), 1)
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
