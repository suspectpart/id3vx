from datetime import timedelta
import unittest
from io import BytesIO

from id3vx.frame import FrameHeader, Frame, TextFrame, PrivateFrame, \
    Frames, AttachedPictureFrame as ApicFrame, \
    ChapterFrame, MusicCDIdentifierFrame, MusicMatchMysteryFrame, CommentFrame
from id3vx.tag import TagHeader


class FramesTests(unittest.TestCase):
    def test_reads_frames_from_file(self):
        # Arrange
        header_a = FrameHeader(b"TALB", 9, FrameHeader.Flags.Compression)
        frame_a = PrivateFrame(header_a, b'\x00thealbum')
        header_b = FrameHeader(b"TIT2", 10, FrameHeader.Flags.Encryption)
        frame_b = PrivateFrame(header_b, b'\x00theartist')
        tag_header = TagHeader(b'ID3', 3, 0, TagHeader.Flags(0), 39)

        byte_string = bytes(frame_a) + bytes(frame_b)

        # Act
        frames = Frames.from_file(BytesIO(byte_string), tag_header)

        # Assert
        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[0].id(), 'TALB')
        self.assertEqual(frames[0].text(), 'thealbum')
        self.assertEqual(frames[1].id(), 'TIT2')
        self.assertEqual(frames[1].text(), 'theartist')

    def test_handles_padding(self):
        """Stops on first padding frame"""
        # Arrange
        header = FrameHeader(b"TALB", 9, FrameHeader.Flags.Compression)
        frame = PrivateFrame(header, b'\x00thealbum')
        padding = b'\x00' * 81
        tag_header = TagHeader(b'ID3', 3, 0, TagHeader.Flags(0), 100)

        byte_string = bytes(frame) + padding

        # Act
        frames = Frames.from_file(BytesIO(byte_string), tag_header)

        # Assert
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].id(), 'TALB')
        self.assertEqual(frames[0].text(), 'thealbum')


class FrameHeaderTests(unittest.TestCase):
    def test_reads_header_from_stream(self):
        """Reads FrameHeader from a bytes stream"""
        # Arrange
        frame_id = b'PRIV'
        size = b'\x00\x00\x00\xFF'
        flags = b'\x00\x00'

        stream = BytesIO(frame_id + size + flags)

        # Act
        header = FrameHeader.from_file(stream)

        # Assert
        self.assertEqual(header.frame_size(), 255)
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
        header = FrameHeader.from_file(stream)

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
        header = FrameHeader.from_file(stream)

        # Assert
        self.assertIn(FrameHeader.Flags.Compression, header.flags())
        self.assertIn(FrameHeader.Flags.Encryption, header.flags())
        self.assertIn(FrameHeader.Flags.GroupingIdentity, header.flags())

    def test_reads_header_if_size_bigger_than_zero(self):
        """Reads FrameHeader as long as size is present"""
        # Arrange
        frame_id = b'\x00\x00\x00\x00'
        frame_size = b'\x00\x00\x00\x01'
        flags = b'\x00\x00'

        stream = BytesIO(frame_id + frame_size + flags)

        # Act
        header = FrameHeader.from_file(stream)

        # Assert
        self.assertEqual(header.frame_size(), 1)
        self.assertEqual(header.id(), frame_id)
        self.assertEqual(header.flags(), FrameHeader.Flags(0))

    def test_no_header_from_too_short_stream(self):
        """Fails to read FrameHeader from a too short byte stream"""
        # Arrange
        frame_id = b'PRIV'
        size = b'\x00\x00\x00\xFF'

        stream = BytesIO(frame_id + size)

        # Act
        header = FrameHeader.from_file(stream)

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
        header = FrameHeader.from_file(stream)

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


class FrameTests(unittest.TestCase):
    def test_represents_every_frame_id(self):
        """Represents every Frame ID"""
        # Arrange - Act - Assert
        self.assertTrue(Frame.represents(b'TXXX'))
        self.assertTrue(Frame.represents(b'TALB'))
        self.assertTrue(Frame.represents(b'WXXX'))
        self.assertTrue(Frame.represents(b'WOAR'))
        self.assertTrue(Frame.represents(b'COMM'))
        self.assertTrue(Frame.represents(b'PRIV'))
        self.assertTrue(Frame.represents(b'????'))

    def test_exposes_fields(self):
        """Exposes relevant fields"""
        # Arrange
        frame_size = 100
        header = FrameHeader(b'PRIV', frame_size, 0)
        fields = b'\x0a\x0f\x00\x0f\x0c'

        # System under test
        frame = Frame(header, fields)

        # Assert
        self.assertEqual(frame.header(), header)
        self.assertEqual(frame.id(), "PRIV")
        self.assertEqual(frame.fields(), fields)
        self.assertEqual(str(frame), str(fields))
        self.assertEqual(len(frame), frame_size + len(header))
        self.assertEqual(frame.name(), "Private frame")

    def test_serializes_to_bytes(self):
        """Serializes itself to bytes"""
        # Arrange
        header = FrameHeader(b'PRIV', 100, 0)
        header_bytes = bytes(header)
        fields = b'\x0a\x0f\x00\x0f\x0c'

        # System under test
        frame = Frame(header, fields)

        # Act
        byte_string = bytes(frame)

        # Assert
        self.assertEqual(byte_string, header_bytes + fields)

    def test_defaults_name_to_identifier(self):
        """Defaults to Frame ID if name is unknown"""
        # Arrange
        header = FrameHeader(b'ABCD', 100, 0)
        fields = b'\x0a\x0f\x00\x0f\x0c'

        # System under test
        frame = Frame(header, fields)

        # Act - Assert
        self.assertEqual(frame.name(), "ABCD")

    def test_no_frame_if_header_invalid(self):
        """Defaults to Frame ID if name is unknown"""
        # Arrange
        broken_header = bytes(10)
        fields = bytes(100)

        stream = BytesIO(broken_header + fields)

        # System under test
        frame = Frame.from_file(stream)

        # Act - Assert
        self.assertIsNone(frame)

    def test_read_frame_from_stream(self):
        """Defaults to Frame ID if name is unknown"""
        # Arrange
        fields = b'\x00Album'
        size = len(fields)
        header = FrameHeader(b'TALB', size, 0)
        frame = TextFrame(header, fields)

        stream = BytesIO(bytes(frame))

        # System under test
        frame = Frame.from_file(stream)

        # Act - Assert
        self.assertEqual(type(frame), TextFrame)
        self.assertEqual(frame.id(), "TALB")
        self.assertEqual(frame.text(), "Album")


class AttachedPictureFrameTests(unittest.TestCase):
    def test_initialize_from_fields(self):
        # Arrange
        header = FrameHeader(b'APIC', 1000, 0)

        encoding = b'\x02'
        mime_type = b'image/paper\x00'
        picture_type = b'\x11'  # bright colored fish
        description = "You can see a fish here"
        desc_bytes = description.encode("utf-16-be") + b'\x00\x00'
        data = b'\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01'

        fields = encoding + mime_type + picture_type + desc_bytes + data

        expected_pic_type = ApicFrame.PictureType.BRIGHT_COLORED_FISH
        expected_mime_type = "image/paper"

        # System under test
        frame = ApicFrame(header, fields)

        # Act - Assert
        self.assertEqual(type(frame), ApicFrame)
        self.assertEqual(frame.description(), description)
        self.assertEqual(frame.picture_type(), expected_pic_type)
        self.assertEqual(frame.mime_type(), "image/paper")
        self.assertEqual(frame.data(), data)

        self.assertIn(description, str(frame))
        self.assertIn(str(data), str(frame))
        self.assertIn(str(expected_pic_type), str(frame))
        self.assertIn(expected_mime_type, str(frame))


class ChapterFrameTests(unittest.TestCase):
    def test_initialize_from_fields(self):
        # Arrange
        header = FrameHeader(b'CHAP', 1000, 0)

        element_id = 'chp'
        element_id_bytes = element_id.encode("latin1")

        t_start = b'\x00\xFF\xFF\xEE'
        t_end = b'\x00\x0A\x0F\xEE'
        o_start = b'\x00\xFF\xFF\xEE'
        o_end = b'\x00\x0A\x0F\xEE'

        delta_start = timedelta(milliseconds=int.from_bytes(t_start, "big"))
        delta_end = timedelta(milliseconds=int.from_bytes(t_end, "big"))
        offset_start = int.from_bytes(o_start, "big")
        offset_end = int.from_bytes(t_end, "big")

        fields = element_id_bytes + b'\x00' + t_start + t_end + o_start + o_end

        expected_bytes = bytes(header) + fields

        # System under test
        frame = ChapterFrame(header, fields)

        # Act - Assert
        self.assertEqual(type(frame), ChapterFrame)
        self.assertEqual(frame.element_id(), element_id)
        self.assertEqual(frame.start(), delta_start)
        self.assertEqual(frame.end(), delta_end)
        self.assertEqual(frame.offset_start(), offset_start)
        self.assertEqual(frame.offset_end(), offset_end)
        self.assertEqual(bytes(frame), expected_bytes)

        self.assertIn(element_id, str(frame))
        self.assertIn(str(delta_start), str(frame))
        self.assertIn(str(delta_end), str(frame))
        self.assertIn(str(offset_start), str(frame))
        self.assertIn(str(offset_end), str(frame))

    def test_subframes(self):
        # Arrange
        sub_frame_header = FrameHeader(b'TIT2', 1000, 0)
        sub_frame = TextFrame(sub_frame_header, b'\x00sometext')

        header = FrameHeader(b'CHAP', 1000, 0)

        element_id = 'chp'
        element_id_bytes = element_id.encode("latin1")

        t_start = b'\x00\xFF\xFF\xEE'
        t_end = b'\x00\x0A\x0F\xEE'
        o_start = b'\x00\xFF\xFF\xEE'
        o_end = b'\x00\x0A\x0F\xEE'

        fields = element_id_bytes + b'\x00' + t_start + t_end + o_start + o_end
        fields += bytes(sub_frame)

        # System under test
        frame = ChapterFrame(header, fields)

        # Act
        sub_frames = list(frame.sub_frames())

        # Act - Assert
        self.assertEqual(1, len(sub_frames))
        self.assertEqual('TIT2', sub_frames[0].id())
        self.assertEqual("sometext", sub_frames[0].text())


class MusicCDIdentifierFrameTests(unittest.TestCase):
    def test_exposes_toc(self):
        # Arrange
        header = FrameHeader(b'MCDI', 1000, 0)
        fields = b'\xf0\xfa\xccsometocdata\xff'

        # System under test
        frame = MusicCDIdentifierFrame(header, fields)

        # Act - Assert
        self.assertEqual(type(frame), MusicCDIdentifierFrame)
        self.assertEqual(fields, frame.toc())
        self.assertTrue(frame.represents(b'MCDI'))


class MusicMatchMysteryFrameTests(unittest.TestCase):
    def test_exposes_toc(self):
        # Arrange
        header = FrameHeader(b'MCDI', 1000, 0)
        fields = b'\xf0\xfa\xccweirdbinaryblob\xff'

        # System under test
        frame = MusicMatchMysteryFrame(header, fields)

        # Act - Assert
        self.assertEqual(type(frame), MusicMatchMysteryFrame)
        self.assertEqual(fields, frame.fields())
        self.assertTrue(frame.represents(b'NCON'))


class CommentFrameTests(unittest.TestCase):
    def test_reads_from_file(self):
        # Arrange
        header = b'COMM\x00\x00\x00\x0a\x00\x00'
        fields = b'\x01\x65\x6e\x67\xff\xfe\x00\x00\xff\xfe'

        stream = BytesIO(header + fields)

        # Act
        frame = Frame.from_file(stream)

        # Assert
        self.assertEqual(type(frame), CommentFrame)
        self.assertEqual(frame.id(), 'COMM')
        self.assertEqual(frame.language(), 'eng')
        self.assertEqual(frame.description(), '')
        self.assertEqual(frame.comment(), '')
