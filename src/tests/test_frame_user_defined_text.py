import unittest
from io import BytesIO

from id3vx.frame import FrameHeader, TXXX


class UserDefinedTextFrameTests(unittest.TestCase):
    def test_decodes_utf_16_text(self):
        """Decodes utf-16 encoded text"""
        # Arrange
        header = FrameHeader('TXXX', 0x00FA, 0, False)
        encoding = b'\x01'
        terminator = b'\x00\x00'
        description = "Specific Text".encode("utf-16")
        text = "Lörem Ipsüm".encode("utf-16")

        fields = encoding + description + terminator + text
        stream = BytesIO(bytes(header) + fields)

        # Act
        frame = TXXX.read(stream)

        # Assert
        self.assertEqual(frame.text, text.decode("utf-16"))
        self.assertEqual(frame.description, description.decode("utf-16"))
        self.assertIn(text.decode("utf-16"), repr(frame))
        self.assertIn(description.decode("utf-16"), repr(frame))

    def test_decodes_utf_8_text(self):
        """Decodes uzf-8 encoded text"""
        # Arrange
        header = FrameHeader('TXXX', 0x00FA, 0, False)
        encoding = b'\x03'
        terminator = b'\x00'
        description = "Specific Text".encode("utf-8")
        text = "Lörem Ipsüm".encode("utf-8")

        fields = encoding + description + terminator + text
        stream = BytesIO(bytes(header) + fields)

        # Act
        frame = TXXX.read(stream)

        # Assert
        self.assertEqual(frame.text, text.decode("utf-8"))
        self.assertEqual(frame.description, description.decode("utf-8"))
        self.assertIn(text.decode("utf-8"), repr(frame))
        self.assertIn(description.decode("utf-8"), repr(frame))

    def test_decodes_utf_8_text_no_description(self):
        """Decodes Latin1 encoded text"""
        # Arrange
        header = FrameHeader('TXXX', 0x00FA, 0, False)
        encoding = b'\x03'
        terminator = b'\x00'
        description = b''
        text = "Lörem Ipsüm".encode("utf-8")

        fields = encoding + description + terminator + text + terminator
        stream = BytesIO(bytes(header) + fields)

        # Act
        frame = TXXX.read(stream)

        # Assert
        self.assertEqual(frame.text, text.decode("utf-8"))
        self.assertEqual(frame.description, "")
        self.assertIn(text.decode("utf-8"), repr(frame))
