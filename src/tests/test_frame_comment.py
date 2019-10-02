import unittest

from id3vx.frame import FrameHeader, CommentFrame


class CommentFrameTests(unittest.TestCase):
    def test_decodes_fields(self):
        """Decodes all comment frame fields"""
        # Arrange
        encoding = "utf-16"
        header = FrameHeader(b'COMM', 0x00FA, 0)

        term = b'\x00\x00'
        codec = b'\x01'
        language = "eng".encode("latin1")
        description = "descriptiön".encode(encoding)
        comment = "Some cömment".encode(encoding)

        fields = codec + language + description + term + comment + term

        # System under test
        frame = CommentFrame(header, fields)

        # Assert
        self.assertEqual(frame.comment(), comment.decode(encoding))
        self.assertEqual(frame.description(), description.decode(encoding))
        self.assertEqual(frame.language(), language.decode("latin1"))
        self.assertIn(language.decode("latin1"), str(frame))
        self.assertIn(description.decode(encoding), str(frame))
        self.assertIn(comment.decode(encoding), str(frame))

    def test_allow_empty_comment_and_description(self):
        """Allows empty comment and description"""
        # Arrange
        encoding = "utf-16"
        header = FrameHeader(b'COMM', 0x00FA, 0)

        term = b'\x00\x00'
        codec = b'\x01'
        language = "eng".encode("latin1")
        description = b''
        comment = b''

        fields = codec + language + description + term + comment + term

        # System under test
        frame = CommentFrame(header, fields)

        # Assert
        self.assertEqual(frame.comment(), "")
        self.assertEqual(frame.description(), "")
        self.assertEqual(frame.language(), language.decode("latin1"))

    def test_represents_comment_frames(self):
        """Represents Frame ID 'COMM'"""
        # System under test
        frame = CommentFrame

        # Act - Assert
        self.assertTrue(frame.represents(b'COMM'))
        self.assertFalse(frame.represents(b'TALB'))
        self.assertFalse(frame.represents(b'TIT2'))
        self.assertFalse(frame.represents(b'PRIV'))
        self.assertFalse(frame.represents(b'WXXX'))
