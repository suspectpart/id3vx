import unittest

from id3vx.frame import FrameHeader, COMM


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
        frame = COMM.read_fields(header, fields)

        # Assert
        self.assertEqual(frame.comment, comment.decode(encoding))
        self.assertEqual(frame.description, description.decode(encoding))
        self.assertEqual(frame.language, language.decode("latin1"))
        self.assertIn(language.decode("latin1"), repr(frame))
        self.assertIn(description.decode(encoding), repr(frame))
        self.assertIn(comment.decode(encoding), repr(frame))

    def test_allow_empty_comment_and_description(self):
        """Allows empty comment and description"""
        # Arrange
        header = FrameHeader(b'COMM', 0x00FA, 0)

        term = b'\x00\x00'
        codec = b'\x01'
        language = "eng".encode("latin1")
        description = b''
        comment = b''

        fields = codec + language + description + term + comment + term

        # System under test
        frame = COMM.read_fields(header, fields)

        # Assert
        self.assertEqual(frame.comment, "")
        self.assertEqual(frame.description, "")
        self.assertEqual(frame.language, language.decode("latin1"))
