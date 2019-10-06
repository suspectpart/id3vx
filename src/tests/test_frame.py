import unittest
from io import BytesIO

from id3vx.frame import FrameHeader, Frame, TextFrame, Frames, PCNT
from id3vx.frame import CHAP, MCDI, NCON, COMM, TALB, APIC, PRIV
from id3vx.tag import TagHeader


class FramesTests(unittest.TestCase):
    def test_reads_frames_from_file(self):
        # Arrange
        header_a = FrameHeader("TALB", 9, FrameHeader.Flags.Compression, False)
        frame_a = PRIV.read(BytesIO(bytes(header_a) + b'\x00thealbum'))
        header_b = FrameHeader("TIT2", 10, FrameHeader.Flags.Encryption, False)
        frame_b = PRIV.read(BytesIO(bytes(header_b) + b'\x00theartist'))
        tag_header = TagHeader('ID3', 3, 0, TagHeader.Flags(0), 39)

        byte_string = bytes(frame_a) + bytes(frame_b)
        stream = BytesIO(byte_string)

        # Act
        frames = Frames.read(stream, tag_header)

        # Assert
        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[0].id(), 'TALB')
        self.assertEqual(frames[0].text, 'thealbum')
        self.assertEqual(frames[1].id(), 'TIT2')
        self.assertEqual(frames[1].text, 'theartist')

    def test_handles_padding(self):
        """Stops on first padding frame"""
        # Arrange
        header = FrameHeader("TALB", 9, FrameHeader.Flags.Compression, False)
        fields = b'\x00thealbum'
        stream = BytesIO(bytes(header) + fields)
        frame = PRIV.read(stream)
        padding = b'\x00' * 81
        tag_header = TagHeader('ID3', 3, 0, TagHeader.Flags(0), 100)

        byte_string = bytes(frame) + padding

        # Act
        frames = Frames.read(BytesIO(byte_string), tag_header)

        # Assert
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].id(), 'TALB')
        self.assertEqual(frames[0].text, 'thealbum')


class FrameHeaderTests(unittest.TestCase):
    def test_reads_header_from_stream(self):
        """Reads FrameHeader from a bytes stream"""
        # Arrange
        frame_id = b'PRIV'
        size = b'\x00\x00\x00\xFF'
        flags = b'\x00\x00'

        stream = BytesIO(frame_id + size + flags)

        # Act
        header = FrameHeader.read(stream)

        # Assert
        self.assertEqual(header.frame_size, 255)
        self.assertEqual(header.flags, FrameHeader.Flags(0))
        self.assertEqual(header.identifier, "PRIV")

    def test_read_synchsafe_size(self):
        """Reads FrameHeader from a bytes stream"""
        # Arrange
        frame_id = b'PRIV'
        size = b'\x00\x00\x02\x01'  # would be 513 in plain binary
        flags = b'\x00\x00'

        expected_size = 257  # ... but is 257 in synchsafe world

        stream = BytesIO(frame_id + size + flags)

        # Act
        header = FrameHeader.read(stream, synchsafe_size=True)

        # Assert
        self.assertEqual(header.frame_size, expected_size)

    def test_reads_all_flags(self):
        """Reads all flags correctly"""
        # Arrange
        frame_id = b'PRIV'
        size = b'\x00\x00\x00\xFF'
        flags = 0b1110000011100000.to_bytes(2, "big")

        stream = BytesIO(frame_id + size + flags)

        # Act
        header = FrameHeader.read(stream)

        # Assert
        self.assertIn(FrameHeader.Flags.Compression, header.flags)
        self.assertIn(FrameHeader.Flags.Encryption, header.flags)
        self.assertIn(FrameHeader.Flags.FileAlterPreservation, header.flags)
        self.assertIn(FrameHeader.Flags.GroupingIdentity, header.flags)
        self.assertIn(FrameHeader.Flags.ReadOnly, header.flags)
        self.assertIn(FrameHeader.Flags.TagAlterPreservation, header.flags)

    def test_reads_some_flags(self):
        """Reads some flags correctly"""
        # Arrange
        frame_id = b'PRIV'
        size = b'\x00\x00\x00\xFF'
        flags = 0b0000000011100000.to_bytes(2, "big")

        stream = BytesIO(frame_id + size + flags)

        # Act
        header = FrameHeader.read(stream)

        # Assert
        self.assertIn(FrameHeader.Flags.Compression, header.flags)
        self.assertIn(FrameHeader.Flags.Encryption, header.flags)
        self.assertIn(FrameHeader.Flags.GroupingIdentity, header.flags)

    def test_reads_header_if_size_bigger_than_zero(self):
        """Reads FrameHeader as long as size is present"""
        # Arrange
        frame_id = b'\x00\x00\x00\x00'
        frame_size = b'\x00\x00\x00\x01'
        flags = b'\x00\x00'

        stream = BytesIO(frame_id + frame_size + flags)

        # Act
        header = FrameHeader.read(stream)

        # Assert
        self.assertEqual(header.frame_size, 1)
        self.assertEqual(header.identifier, frame_id.decode("latin1"))
        self.assertEqual(header.flags, FrameHeader.Flags(0))

    @unittest.SkipTest
    def test_no_header_from_too_short_stream(self):
        """Fails to read FrameHeader from a too short byte stream"""
        # Arrange
        frame_id = b'PRIV'
        size = b'\x00\x00\x00\xFF'

        stream = BytesIO(frame_id + size)

        # Act
        header = FrameHeader.read(stream)

        # Assert
        self.assertFalse(bool(header))  # TODO: fix this with proper None

    def test_reads_no_header_if_size_is_zero(self):
        """Fails to read FrameHeader if size is zero"""
        # Arrange
        frame_id = b'PRIV'
        size = b'\x00\x00\x00\x00'
        flags = b'\x00\x00'

        stream = BytesIO(frame_id + size + flags)

        # Act
        header = FrameHeader.read(stream)

        # Assert
        self.assertFalse(header)

    def test_converts_back_to_bytes(self):
        # Arrange
        frame_id = 'PRIV'
        size = 3333
        flags = 0b1100_0000_0000_0000

        expected_bytes = b'PRIV\x00\x00\r\x05\xc0\x00'

        # System under test
        header = FrameHeader(frame_id, size, flags, False)

        # Act
        header_bytes = bytes(header)

        # Assert
        self.assertEqual(header_bytes, expected_bytes)


class FrameTests(unittest.TestCase):
    def test_exposes_fields(self):
        """Exposes relevant fields"""
        # Arrange
        frame_size = 100
        header = FrameHeader('PRIV', frame_size, 0, False)
        fields = b'\x0a\x0f\x00\x0f\x0c'

        # System under test
        frame = Frame(header, fields)

        # Assert
        self.assertEqual(frame.header, header)
        self.assertEqual(frame.id(), "PRIV")
        self.assertEqual(frame.fields, fields)
        self.assertIn(str(fields), repr(frame))
        self.assertEqual(len(frame), frame_size + len(header))

    def test_serializes_to_bytes(self):
        """Serializes itself to bytes"""
        # Arrange
        header = FrameHeader('PRIV', 100, 0, False)
        header_bytes = bytes(header)
        fields = b'\x0a\x0f\x00\x0f\x0c'

        # System under test
        frame = Frame(header, fields)

        # Act
        byte_string = bytes(frame)

        # Assert
        self.assertEqual(byte_string, header_bytes + fields)

    def test_no_frame_if_header_invalid(self):
        """Defaults to Frame ID if name is unknown"""
        # Arrange
        broken_header = bytes(10)
        fields = bytes(100)

        stream = BytesIO(broken_header + fields)

        # System under test
        frame = Frame.read(stream)

        # Act - Assert
        self.assertIsNone(frame)

    def test_read_frame_from_stream(self):
        """Defaults to Frame ID if name is unknown"""
        # Arrange
        fields = b'\x00Album'
        size = len(fields)
        header = FrameHeader('TALB', size, 0, False)
        frame = TextFrame.read(BytesIO(bytes(header) + fields))

        stream = BytesIO(bytes(frame))

        # System under test
        frame = Frame.read(stream)

        # Act - Assert
        self.assertEqual(type(frame), TALB)
        self.assertEqual(frame.text, "Album")


class APICTests(unittest.TestCase):
    def test_initialize_from_fields(self):
        # Arrange
        header = FrameHeader('APIC', 1000, 0, False)

        encoding = b'\x02'
        mime_type = b'image/paper\x00'
        picture_type = b'\x11'  # bright colored fish
        description = "You can see a fish here"
        desc_bytes = description.encode("utf-16-be") + b'\x00\x00'
        data = b'\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01'

        fields = encoding + mime_type + picture_type + desc_bytes + data

        expected_pic_type = APIC.PictureType.BRIGHT_COLORED_FISH
        expected_mime_type = "image/paper"

        # System under test
        frame = APIC.read(BytesIO(bytes(header) + fields))

        # Act - Assert
        self.assertEqual(type(frame), APIC)
        self.assertEqual(frame.description, description)
        self.assertEqual(frame.picture_type, expected_pic_type)
        self.assertEqual(frame.mime_type, "image/paper")
        self.assertEqual(frame.data, data)

        self.assertIn(description, repr(frame))
        self.assertIn(str(data), repr(frame))
        self.assertIn(str(expected_pic_type), repr(frame))
        self.assertIn(expected_mime_type, repr(frame))


class CHAPTests(unittest.TestCase):
    def test_initialize_from_fields(self):
        # Arrange
        header = FrameHeader('CHAP', 1000, 0, False)

        element_id = 'chp'
        element_id_bytes = element_id.encode("latin1")
        t_start = b'\x00\xFF\xFF\xEE'
        t_end = b'\x00\x0A\x0F\xEE'
        o_start = b'\x00\xFF\xFF\xEE'
        o_end = b'\x00\x0A\x0F\xEE'
        offset_start = int.from_bytes(o_start, "big")
        offset_end = int.from_bytes(t_end, "big")

        fields = element_id_bytes + b'\x00' + t_start + t_end + o_start + o_end

        expected_bytes = bytes(header) + fields
        stream = BytesIO(bytes(header) + fields)

        # System under test
        frame = CHAP.read(stream)

        # Act - Assert
        self.assertEqual(type(frame), CHAP)
        self.assertEqual(frame.element_id, element_id)
        self.assertEqual(frame.start_time, 0xFFFFEE)
        self.assertEqual(frame.end_time, 0x0A0FEE)
        self.assertEqual(frame.start_offset, offset_start)
        self.assertEqual(frame.end_offset, offset_end)
        self.assertEqual(bytes(frame), expected_bytes)

    def test_subframes(self):
        """FIXME: this test sucks"""
        # Arrange
        sub_fields = b'\x00sometext\x00'
        sub_header = FrameHeader('TIT2', 1000, 0, False)
        sub_frame = TextFrame.read(BytesIO(bytes(sub_header) + sub_fields))

        header = FrameHeader('CHAP', 1000, 0, False)

        element_id = 'chp'
        element_id_bytes = element_id.encode("latin1")

        t_start = b'\x00\xFF\xFF\xEE'
        t_end = b'\x00\x0A\x0F\xEE'
        o_start = b'\x00\xFF\xFF\xEE'
        o_end = b'\x00\x0A\x0F\xEE'

        fields = element_id_bytes + b'\x00' + t_start + t_end + o_start + o_end
        fields += bytes(sub_frame)

        # System under test
        frame = CHAP.read(BytesIO(bytes(header) + fields))

        # Act
        sub_frames = list(frame.sub_frames())

        # Act - Assert
        self.assertEqual(1, len(sub_frames))
        self.assertEqual('TIT2', sub_frames[0].id())
        self.assertEqual("sometext", sub_frames[0].text)


class MCDITests(unittest.TestCase):
    def test_exposes_toc(self):
        # Arrange
        header = FrameHeader('MCDI', 1000, 0, False)
        fields = b'\xf0\xfa\xccsometocdata\xff'
        stream = BytesIO(bytes(header) + fields)

        # System under test
        frame = MCDI.read(stream)

        # Act - Assert
        self.assertEqual(type(frame), MCDI)
        self.assertEqual(fields, frame.toc)


class NCONTests(unittest.TestCase):
    def test_recognizes_music_match_frames(self):
        # Arrange
        header = FrameHeader('NCON', 1000, 0, False)
        fields = b'\xf0\xfa\xccweirdbinaryblob\xff'
        stream = BytesIO(bytes(header) + fields)

        # System under test
        frame = NCON.read(stream)

        # Act - Assert
        self.assertEqual(type(frame), NCON)


class COMMTests(unittest.TestCase):
    def test_reads_from_file(self):
        # Arrange
        header = b'COMM\x00\x00\x00\x0a\x00\x00'
        fields = b'\x01\x65\x6e\x67\xff\xfe\x00\x00\xff\xfe'
        stream = BytesIO(header + fields)

        # Act
        frame = COMM.read(stream)

        # Assert
        self.assertEqual(type(frame), COMM)
        self.assertEqual(frame.id(), 'COMM')
        self.assertEqual(frame.language, 'eng')
        self.assertEqual(frame.description, '')
        self.assertEqual(frame.comment, '')


class PCNTTests(unittest.TestCase):
    def test_reads_pcnt_frame_from_stream(self):
        """Counts all 18446744073709550304 plays of Old Time Road"""
        # Arrange
        header = b'PCNT\x00\x00\x00\x0a\x00\x00'
        fields = b'\xff\xff\xff\xff\xff\xff\xfa\xe0'
        expected_play_count = 0xfffffffffffffae0
        stream = BytesIO(header + fields)

        # Act
        frame = PCNT.read(stream)

        # Assert
        self.assertEqual(type(frame), PCNT)
        self.assertEqual(frame.counter, expected_play_count)
