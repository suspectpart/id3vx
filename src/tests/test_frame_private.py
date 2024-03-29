import unittest
from io import BytesIO

from id3vx.frame import FrameHeader, PRIV


class PrivateFrameTests(unittest.TestCase):
    def test_exposes_all_fields(self):
        """Exposes all fields properly"""
        # Arrange
        header = FrameHeader('PRIV', 0x00FA, 0, False)
        owner = "horst"
        random_binary = b'\xfa\x0a\x0c\x00\x00\xff\xca'
        fields = bytes(owner, "latin1") + b'\x00' + random_binary

        stream = BytesIO(bytes(header) + fields)

        # Act
        frame = PRIV.read(stream)

        # Assert
        self.assertEqual(frame.header, header)
        self.assertEqual(frame.data, random_binary)
        self.assertEqual(frame.owner, owner)
        self.assertIn(str(random_binary), repr(frame))
        self.assertIn(owner, repr(frame))
