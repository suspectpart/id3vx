import unittest

from id3vx.codec import Codec
from id3vx.frame import Frames, TextFrame, FrameHeader
from id3vx.tag import Tag, TagHeader


class TagTests(unittest.TestCase):
    def test_initializes(self):
        # Arrange
        size = 10000
        flags = TagHeader.Flags.Experimental

        header = TagHeader('ID3', 3, 2, flags, 10000)
        frames = Frames([])

        # System under test
        tag = Tag(header, frames)

        self.assertEqual(tag.header(), header)
        self.assertEqual(list(tag), frames)
        self.assertEqual(len(tag), size + 10)

    def test_serialize_to_bytes(self):
        # Arrange
        flags = TagHeader.Flags.Experimental
        codec = Codec.default()

        tag_header = TagHeader('ID3', 3, 2, flags, 18)

        frame_header = FrameHeader('TALB', 10, 0, False)
        frame = TextFrame(frame_header, codec, "sometext")

        expected_bytes = bytes(tag_header) + bytes(frame)

        # System under test
        tag = Tag(tag_header, Frames([frame]))

        # Act
        byte_string = bytes(tag)

        self.assertEqual(byte_string, expected_bytes)
