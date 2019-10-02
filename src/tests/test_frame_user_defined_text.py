import unittest

from id3vx.frame import FrameHeader, UserDefinedTextFrame


class UserDefinedTextFrameTests(unittest.TestCase):
    def test_decodes_frames_with_null_terminator(self):
        """Decodes Latin1 encoded text"""
        # Arrange
        header = FrameHeader(b'TXXX', 0x00FA, 0)
        encoding = b'\x01'
        terminator = b'\x00\x00'
        description = "Specific Text".encode("utf-16")
        text = "Lörem Ipsüm".encode("utf-16")

        fields = encoding + description + terminator + text + terminator

        # Act
        frame = UserDefinedTextFrame(header, fields)

        # Assert
        self.assertEqual(frame.text(), text.decode("utf-16"))
        self.assertEqual(frame.description(), description.decode("utf-16"))
        self.assertIn(text.decode("utf-16"), str(frame))
        self.assertIn(description.decode("utf-16"), str(frame))

    def test_decodes_latin1_frames_without_null_terminator(self):
        """Decodes Latin1 encoded text"""
        # Arrange
        header = FrameHeader(b'TXXX', 0x00FA, 0)
        encoding = b'\x03'
        terminator = b'\x00'
        description = "Specific Text".encode("utf-8")
        text = "Lörem Ipsüm".encode("utf-8")

        fields = encoding + description + terminator + text

        # Act
        frame = UserDefinedTextFrame(header, fields)

        # Assert
        self.assertEqual(frame.text(), text.decode("utf-8"))
        self.assertEqual(frame.description(), description.decode("utf-8"))
        self.assertIn(text.decode("utf-8"), str(frame))
        self.assertIn(description.decode("utf-8"), str(frame))

    def test_decodes_frames_with_empty_description(self):
        """Decodes Latin1 encoded text"""
        # Arrange
        header = FrameHeader(b'TXXX', 0x00FA, 0)
        encoding = b'\x03'
        terminator = b'\x00'
        description = b''
        text = "Lörem Ipsüm".encode("utf-8")

        fields = encoding + description + terminator + text

        # Act
        frame = UserDefinedTextFrame(header, fields)

        # Assert
        self.assertEqual(frame.text(), text.decode("utf-8"))
        self.assertEqual(frame.description(), "")
        self.assertIn(text.decode("utf-8"), str(frame))

    def test_represents_txxx_text_frame(self):
        """Represents Frame ID 'TXXX'"""
        # System Under Test
        frame = UserDefinedTextFrame

        # Act - Assert
        self.assertTrue(frame.represents(b'TXXX'))
        self.assertFalse(frame.represents(b'TALB'))
        self.assertFalse(frame.represents(b'TIT2'))
        self.assertFalse(frame.represents(b'PRIV'))
        self.assertFalse(frame.represents(b'COMM'))