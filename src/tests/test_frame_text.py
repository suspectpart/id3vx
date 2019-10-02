import unittest

from id3vx.frame import FrameHeader, TextFrame


class TextFrameTests(unittest.TestCase):
    # TODO: what about null terminated strings?
    def test_decodes_latin1_frames_with_null_terminator(self):
        """Decodes Latin1 encoded text"""
        # Arrange
        header = FrameHeader(b'TXXX', 0x00FA, 0)
        encoding = b'\x00'
        text = "Lörem Ipsüm"

        fields = encoding + text.encode("latin1")

        # Act
        frame = TextFrame(header, fields)

        # Assert
        self.assertEqual(frame.text(), text)
        self.assertEqual(str(frame), text)

    def test_decodes_latin1_frames_without_null_terminator(self):
        """Decodes Latin1 encoded text"""
        # Arrange
        header = FrameHeader(b'TXXX', 0x00FA, 0)
        encoding = b'\x00'
        text = "Lörem Ipsüm"

        fields = encoding + text.encode("latin1")

        # Act
        frame = TextFrame(header, fields)

        # Assert
        self.assertEqual(frame.text(), text)
        self.assertEqual(str(frame), text)

    def test_decodes_utf_16_frames(self):
        """Decodes UTF-16 encoded text"""
        # Arrange
        header = FrameHeader(b'TXXX', 0x00FA, 0)
        encoding = b'\x01'
        text = "Lörem Ipsüm"

        fields = encoding + text.encode("utf_16")

        # Act
        frame = TextFrame(header, fields)

        # Assert
        self.assertEqual(frame.text(), text)
        self.assertEqual(str(frame), text)

    def test_decodes_utf_16_be_frames(self):
        """Decodes UTF-16BE encoded text"""
        # Arrange
        header = FrameHeader(b'TXXX', 0x00FA, 0)
        encoding = b'\x02'
        text = "Lörem Ipsüm"

        fields = encoding + text.encode("utf_16_be")

        # Act
        frame = TextFrame(header, fields)

        # Assert
        self.assertEqual(frame.text(), text)
        self.assertEqual(str(frame), text)

    def test_decodes_utf_8_frames(self):
        """Decodes UTF-8 encoded text"""
        # Arrange
        header = FrameHeader(b'TXXX', 0x00FA, 0)
        encoding = b'\x03'
        text = "Lörem Ipsüm"

        fields = encoding + text.encode("utf-8")

        # Act
        frame = TextFrame(header, fields)

        # Assert
        self.assertEqual(frame.text(), text)
        self.assertEqual(str(frame), text)

    def test_represents_every_text_frame(self):
        """Represents every Frame ID starting with 'T'"""
        # System under test
        frame = TextFrame

        # Act - Assert
        self.assertTrue(frame.represents(b'TXXX'))
        self.assertTrue(frame.represents(b'TALB'))
        self.assertTrue(frame.represents(b'TIT2'))
        self.assertFalse(frame.represents(b'PRIV'))
        self.assertFalse(frame.represents(b'COMM'))
