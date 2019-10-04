import unittest

from id3vx.frame import FrameHeader, PRIV


class PrivateFrameTests(unittest.TestCase):
    def test_exposes_all_fields(self):
        """Exposes all fields properly"""
        # Arrange
        header = FrameHeader(b'PRIV', 0x00FA, 0)
        owner = "horst"
        random_binary = b'\xfa\x0a\x0c\x00\x00\xff\xca'
        fields = bytes(owner, "latin1") + b'\x00' + random_binary

        # Act
        frame = PRIV(header, fields)

        # Assert
        self.assertEqual(frame.header(), header)
        self.assertEqual(frame.data(), random_binary)
        self.assertEqual(frame.owner(), owner)
        self.assertIn(str(random_binary), str(frame))
        self.assertIn(owner, str(frame))

    def test_represents_private_frames(self):
        """Represents only PRIV ids"""
        # Arrange - Act - Assert
        self.assertTrue(PRIV.represents(b'PRIV'))
        self.assertFalse(PRIV.represents(b'COMM'))
        self.assertFalse(PRIV.represents(b'TXXX'))
        self.assertFalse(PRIV.represents(b'WXXX'))
