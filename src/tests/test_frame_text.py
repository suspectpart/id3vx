import unittest
from io import BytesIO

from id3vx.frame import FrameHeader, TextFrame


class TextFrameTests(unittest.TestCase):
    def test_decodes_latin1_frames_with_null_terminator(self):
        """Decodes Latin1 encoded text"""
        # Arrange
        header = FrameHeader('TIT2', 0x00FA, 0, False)
        encoding = b'\x00'
        text = "Lörem Ipsüm"

        fields = encoding + text.encode("latin1")
        stream = BytesIO(bytes(header) + fields)

        # Act
        frame = TextFrame.read(stream)

        # Assert
        self.assertEqual(frame.text, text)
        self.assertIn(text, repr(frame))

    def test_decodes_latin1_frames_without_null_terminator(self):
        """Decodes Latin1 encoded text"""
        # Arrange
        header = FrameHeader('TALB', 0x00FA, 0, False)
        encoding = b'\x00'
        text = "Lörem Ipsüm"

        fields = encoding + text.encode("latin1")
        stream = BytesIO(bytes(header) + fields)

        # Act
        frame = TextFrame.read(stream)

        # Assert
        self.assertEqual(frame.text, text)
        self.assertIn(text, repr(frame))

    def test_decodes_utf_16_frames(self):
        """Decodes UTF-16 encoded text"""
        # Arrange
        header = FrameHeader('TALB', 0x00FA, 0, False)
        encoding = b'\x01'
        text = "Lörem Ipsüm"

        fields = encoding + text.encode("utf_16")
        stream = BytesIO(bytes(header) + fields)

        # Act
        frame = TextFrame.read(stream)

        # Assert
        self.assertEqual(frame.text, text)
        self.assertIn(text, repr(frame))

    def test_decodes_utf_16_be_frames(self):
        """Decodes UTF-16BE encoded text"""
        # Arrange
        header = FrameHeader('TALB', 0x00FA, 0, False)
        encoding = b'\x02'
        text = "Lörem Ipsüm"

        fields = encoding + text.encode("utf_16_be")
        stream = BytesIO(bytes(header) + fields)

        # Act
        frame = TextFrame.read(stream)

        # Assert
        self.assertEqual(frame.text, text)
        self.assertIn(text, repr(frame))

    def test_decodes_utf_8_frames(self):
        """Decodes UTF-8 encoded text"""
        # Arrange
        header = FrameHeader('TALB', 0x00FA, 0, False)
        encoding = b'\x03'
        text = "Lörem Ipsüm"
        fields = encoding + text.encode("utf-8")

        stream = BytesIO(bytes(header) + fields)

        # Act
        frame = TextFrame.read(stream)

        # Assert
        self.assertEqual(frame.text, text)
        self.assertIn(text, repr(frame))
