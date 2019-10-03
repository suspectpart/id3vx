import datetime
import enum
import struct
from collections import namedtuple
from enum import IntFlag
from io import BytesIO

from id3vx.binary import unsynchsafe
from .codec import Codec
from .text import shorten


class Frames(list):
    """Represents a all Frames in a Tag."""

    @classmethod
    def from_file(cls, mp3, header):
        """Reads frames from file

        Read consecutive frames up until tag size specified in the header.
        Stops reading frames when an empty (padding) frame is encountered.
        """
        synchsafe_frame_size = header.version()[0] == 4
        frames = []

        while mp3.tell() < header.tag_size():
            frame = Frame.from_file(mp3, synchsafe_frame_size)

            if not frame:
                # stop on first padding frame
                break

            frames.append(frame)

        return cls(frames)

    def __init__(self, args):
        super().__init__(args)


class FrameHeader:
    """A single 10-byte ID3v2.3 frame header.

    Refer to `ID3v2.3 frame header specification
    <http://id3.org/id3v2.3.0#ID3v2_frame_overview>`_
    """

    SIZE = 10

    class Flags(IntFlag):
        """Represents 2-byte flags of the frame header.

         Refer to `ID3v2.3 header flags specification
        <http://id3.org/id3v2.3.0#Frame_header_flags>`_
        """

        TagAlterPreservation = 1 << 15
        FileAlterPreservation = 1 << 14
        ReadOnly = 1 << 13
        Compression = 1 << 7
        Encryption = 1 << 6
        GroupingIdentity = 1 << 5

    @classmethod
    def from_file(cls, mp3, unsynchronize_size=False):
        try:
            block = mp3.read(FrameHeader.SIZE)
            identifier, size, flags = struct.unpack('>4sLH', block)

            # FIXME: hacky, handed down all the way. needs some polymorphism
            size = unsynchsafe(size) if unsynchronize_size else size

            return cls(identifier, size, flags) if size else None
        except struct.error:
            return None

    def __init__(self, identifier, frame_size, flags):
        self._id = identifier
        self._frame_size = frame_size
        self._flags = flags

    def flags(self):
        return FrameHeader.Flags(self._flags)

    def id(self):
        return self._id

    def frame_size(self):
        """Overall frame size excluding the 10 bytes header size"""
        return self._frame_size

    def __repr__(self):
        return f'FrameHeader(id={self.id()},' \
               f'size={self.frame_size()},' \
               f'flags={str(self.flags())})'

    def __bytes__(self):
        return struct.pack('>4sLH',
                           self.id(),
                           self.frame_size(),
                           int(self.flags()))

    def __len__(self):
        return FrameHeader.SIZE


class Frame:
    """An ID3v2.3 frame.

    Refer to `ID3v2.3 frame specification
    <http://id3.org/id3v2.3.0#ID3v2_frame_overview>`_
    """

    @classmethod
    def from_file(cls, mp3, unsynchronize_size=False):
        """Read the next frame from an mp3 file object"""
        header = FrameHeader.from_file(mp3, unsynchronize_size)

        if not header:
            return None

        fields = mp3.read(header.frame_size())
        cls_ = next(f for f in FRAMES_PIPE if f.represents(header.id()))

        return cls_(header, fields)

    @staticmethod
    def represents(identifier):
        return True

    def __init__(self, header, fields):
        self._header = header
        self._fields = fields

    def header(self):
        return self._header

    def fields(self):
        return self._fields

    def id(self):
        """The 4-letter frame id of this frame.

        See `specification <http://id3.org/id3v2.3.0#Declared_ID3v2_frames>`_
        for a full list.
        """
        return Codec.default().decode(self.header().id())

    def name(self):
        """Human-readable name of a frame.

        Defaults to the 4-letter id if name can not be looked up
        (e.g. when it is a custom extension).
        """
        return DECLARED_FRAMES.get(self.id(), self.id())

    def __len__(self):
        """The overall size of the frame in bytes, including header."""
        return len(self.header()) + self.header().frame_size()

    def __str__(self):
        return str(self.fields())

    def __repr__(self):
        return f'{type(self).__name__}(' \
               f'{repr(self.header())},' \
               f'fields="{shorten(str(self), 250)}",size={len(self)})'

    def __bytes__(self):
        return bytes(self.header()) + bytes(self.fields())


class AttachedPictureFrame(Frame):
    """An attached picture frame (APIC)

    <Header for 'Attached picture', ID: "APIC">
    Text encoding   $xx
    MIME type       <text string> $00
    Picture type    $xx
    Description     <text string according to encoding> $00 (00)
    Picture data    <binary data>

    See `specification <http://id3.org/id3v2.3.0#Attached_picture>`_
    """

    class PictureType(enum.Enum):
        OTHER = 0x00                # "Other"
        ICON = 0x01                 # "32x32 pixels 'file icon' (PNG only)"
        OTHER_ICON = 0x02           # "Other file icon"
        FRONT_COVER = 0x03          # "Cover (front)"
        BACK_COVER = 0x04           # "Cover (back)"
        LEAFLET = 0x05              # "Leaflet page"
        MEDIA = 0x06                # "Media (e.g. lable side of CD)"
        LEAD_ARTIST = 0x07          # "Lead artist/lead performer/soloist"
        ARTIST = 0x08               # "Artist/performer"
        CONDUCTOR = 0x09            # "Conductor"
        BAND = 0x0A                 # "Band/Orchestra"
        COMPOSER = 0x0B             # "Composer"
        LYRICIST = 0x0C             # "Lyricist/text writer"
        RECORD_LOCATION = 0x0D      # "Recording Location"
        DURING_LOCATION = 0x0E      # "During recording"
        DURING_PERFORMANCE = 0x0F   # "During performance"
        SCREEN_CAPTURE = 0x10       # "Movie/video screen capture"
        BRIGHT_COLORED_FISH = 0x11  # "A bright coloured fish"
        ILLUSTRATION = 0x12         # "Illustration"
        BAND_LOGO_TYPE = 0x13       # "Band/artist logotype"
        PUBLISHER_LOGO_TYPE = 0x14  # "Publisher/Studio logotype"

    @staticmethod
    def represents(identifier):
        return identifier == b'APIC'

    def __init__(self, header, fields):
        super().__init__(header, fields)

        # There are some tags that contain only null bytes \x00\x00\x00
        # right before the data starts. Parsing them causes all the fields
        # to be slightly off, e.g. the JPEG header slips into the description,
        # reading ÿØÿà. kid3 and eyeD3 Have the same issue, so that seems to
        # be violating spec and it's not just me being stupid.
        self._codec = Codec.get(fields[0])

        mime_type, remainder = Codec.default().split(fields[1:], 1)
        description, self._data = self._codec.split(remainder[1:], 1)

        self._picture_type = self.PictureType(remainder[0])
        self._description = self._codec.decode(description)
        self._mime_type = Codec.default().decode(mime_type)

    def picture_type(self):
        return self._picture_type

    def description(self):
        return self._description

    def mime_type(self):
        return self._mime_type

    def data(self):
        return self._data

    def __str__(self):
        return f"[mime-type={self.mime_type()}]" \
               f"[description={self.description()}]" \
               f"[picture-type={self.picture_type()}]" \
               f"[data={self.data()}]"


class MusicCDIdentifierFrame(Frame):
    """A Music CD Identifier Frame (MCDI)

    See `specification <http://id3.org/id3v2.3.0#Music_CD_identifier>`_
    """

    @staticmethod
    def represents(identifier):
        return identifier == b'MCDI'

    def toc(self):
        """TOC of Music CD"""
        return self.fields()


class MusicMatchMysteryFrame(Frame):
    """A mysterious binary frame added by MusicMatch (NCON)"""

    @staticmethod
    def represents(identifier):
        return identifier == b'NCON'


class PrivateFrame(Frame):
    def __init__(self, header, fields):
        super().__init__(header, fields)

        self._owner, self._data = Codec.default().split(fields, 1)

    @staticmethod
    def represents(identifier):
        return identifier == b'PRIV'

    def owner(self):
        return Codec.default().decode(self._owner)

    def data(self):
        return self._data

    def __str__(self):
        return f'[owner {self.owner()}] {self.data()}'


class UFIDFrame(PrivateFrame):
    """A Unique file identifier frame (UFID)"""

    @staticmethod
    def represents(identifier):
        return identifier == b'UFID'


class TextFrame(Frame):
    """A text frame (T___)

    Decodes all of the frame with the encoding read from the first byte.
    """

    def __init__(self, header, fields):
        super().__init__(header, fields)

        self._codec = Codec.get(fields[0])
        self._text = fields[1:]

    @staticmethod
    def represents(identifier):
        return identifier.startswith(b'T')

    def text(self):
        return self._codec.decode(self._text)

    def __str__(self):
        return self.text()


class PicardFrame(TextFrame):
    """A Special, kind of hacky frame introduced by MusicBrainz Picard (XSO*)

    Can be XSOA, XSOT or XSOP that map to TSOA, TSOT and TSOP in ID3v2.4
    """

    @staticmethod
    def represents(identifier):
        return identifier in [b'XSOA', b'XSOP', b'XSOT']


class UserDefinedTextFrame(TextFrame):
    def __init__(self, header, fields):
        super().__init__(header, fields)

        self._description, self._text = self._codec.split_decode(fields[1:], 2)

    @staticmethod
    def represents(identifier):
        return identifier == b'TXXX'

    def text(self):
        return self._text

    def description(self):
        return self._description

    def __str__(self):
        return f'[description {self.description()}] {self.text()}'


class URLLinkFrame(Frame):
    def __str__(self):
        return Codec.default().decode(self.fields())

    @staticmethod
    def represents(identifier):
        return identifier == b'WOAR'


class UserDefinedURLLinkFrame(TextFrame):
    """A User Defined URL Frame (WXXX)

    Reads comment and description from an already decoded TextFrame.
    """

    def __init__(self, header, fields):
        super().__init__(header, fields)

        self._description, self._url = self._codec.split_decode(fields[1:], 2)

    @staticmethod
    def represents(identifier):
        return identifier == b'WXXX'

    def description(self):
        return self._description

    def url(self):
        return self._url

    def __str__(self):
        return f'[description {self.description()}] {self.url()}'


class CommentFrame(TextFrame):
    """Comment Frame (COMM)

    Reads language, description and comment from an already decoded TextFrame.
    """

    def __init__(self, header, fields):
        super().__init__(header, fields)

        self._language = Codec.default().decode(fields[1:4])

        parts = self._codec.split_decode(fields[4:], 2)
        self._description, self._comment = parts

    @staticmethod
    def represents(identifier):
        return identifier == b'COMM'

    def language(self):
        return self._language

    def description(self):
        return self._description

    def comment(self):
        return self._comment

    def __str__(self):
        return f'[language {self.language()}]' \
               f'[description {self.description()}] ' \
               f'{self.comment()}'


class ChapterFrame(Frame):
    """A Chapter frame (CHAP)

    <ID3v2.3 or ID3v2.4 frame header, ID: "CHAP">           (10 bytes)
    Element ID      <text string> $00
    Start time      $xx xx xx xx
    End time        $xx xx xx xx
    Start offset    $xx xx xx xx
    End offset      $xx xx xx xx
    <Optional embedded sub-frames>

    See `specification <http://id3.org/id3v2-chapters-1.0>`_
    """

    Timings = namedtuple("Timings", "start, end, start_offset, end_offset")

    def __init__(self, header, fields):
        super().__init__(header, fields)

        element_id, remainder = Codec.default().split(fields, 1)

        self._element_id = Codec.default().decode(element_id)
        self._timings = self.Timings(*struct.unpack('>LLLL', remainder[:16]))
        self._sub_frames = remainder[16:]

    @staticmethod
    def represents(identifier):
        return identifier == b'CHAP'

    def sub_frames(self):
        """CHAP frames include 0-2 sub frames (of type TIT2 and TIT3)"""
        with BytesIO(self._sub_frames) as io:
            frames = [Frame.from_file(io), Frame.from_file(io)]

        return (f for f in frames if f)

    def element_id(self):
        return self._element_id

    def start(self):
        return datetime.timedelta(milliseconds=self._timings.start)

    def end(self):
        return datetime.timedelta(milliseconds=self._timings.end)

    def offset_start(self):
        return self._timings.start_offset

    def offset_end(self):
        return self._timings.end_offset

    def __str__(self):
        return f'[{self._element_id}] ' \
               f'start: {self.start()} ' \
               f'end: {self.end()} ' \
               f'start_offset: {self.offset_start()} ' \
               f'end_offset: {self.offset_end()} ' \
               f'sub_frames: {" ".join(repr(f) for f in self.sub_frames())}'

    def __bytes__(self):
        header = bytes(self.header())
        element_id = Codec.default().encode(self._element_id)
        timings = struct.pack('>LLLL', *self._timings)

        return header + element_id + timings + self._sub_frames


DECLARED_FRAMES = {
    "AENC": "Audio encryption",
    "APIC": "Attached picture",
    "COMM": "Comments",
    "COMR": "Commercial frame",
    "ENCR": "Encryption method registration",
    "EQUA": "Equalization",
    "ETCO": "Event timing codes",
    "GEOB": "General encapsulated object",
    "GRID": "Group identification registration",
    "IPLS": "Involved people list",
    "LINK": "Linked information",
    "MCDI": "Music CD identifier",
    "MLLT": "MPEG location lookup table",
    "OWNE": "Ownership frame",
    "PRIV": "Private frame",
    "PCNT": "Play counter",
    "POPM": "Popularimeter",
    "POSS": "Position synchronisation frame",
    "RBUF": "Recommended buffer size",
    "RVAD": "Relative volume adjustment",
    "RVRB": "Reverb",
    "SYLT": "Synchronized lyric/text",
    "SYTC": "Synchronized tempo codes",
    "TALB": "Album/Movie/Show title",
    "TBPM": "BPM (beats per minute)",
    "TCOM": "Composer",
    "TCON": "Content type",
    "TCOP": "Copyright message",
    "TDAT": "Date",
    "TDLY": "Playlist delay",
    "TENC": "Encoded by",
    "TEXT": "Lyricist/Text writer",
    "TFLT": "File type",
    "TIME": "Time",
    "TIT1": "Content group description",
    "TIT2": "Title/songname/content description",
    "TIT3": "Subtitle/Description refinement",
    "TKEY": "Initial key",
    "TLAN": "Language(s)",
    "TLEN": "Length",
    "TMED": "Media type",
    "TOAL": "Original album/movie/show title",
    "TOFN": "Original filename",
    "TOLY": "Original lyricist(s)/text writer(s)",
    "TOPE": "Original artist(s)/performer(s)",
    "TORY": "Original release year",
    "TOWN": "File owner/licensee",
    "TPE1": "Lead performer(s)/Soloist(s)",
    "TPE2": "Band/orchestra/accompaniment",
    "TPE3": "Conductor/performer refinement",
    "TPE4": "Interpreted, remixed, or otherwise modified by",
    "TPOS": "Part of a set",
    "TPUB": "Publisher",
    "TRCK": "Track number/Position in set",
    "TRDA": "Recording dates",
    "TRSN": "Internet radio station name",
    "TRSO": "Internet radio station owner",
    "TSIZ": "Size",
    "TSRC": "ISRC (international standard recording code)",
    "TSSE": "Software/Hardware and settings used for encoding",
    "TYER": "Year",
    "TXXX": "User defined text information frame",
    "UFID": "Unique file identifier",
    "USER": "Terms of use",
    # sic! (typo in spec: Unsychronized must be "Unsynchronized")
    "USLT": "Unsychronized lyric/text transcription",
    "WCOM": "Commercial information",
    "WCOP": "Copyright/Legal information",
    "WOAF": "Official audio file webpage",
    "WOAR": "Official artist/performer webpage",
    "WOAS": "Official audio source webpage",
    "WORS": "Official internet radio station homepage",
    "WPAY": "Payment",
    "WPUB": "Publishers official webpage",
    "WXXX": "User defined URL link frame",
    "XSOT": "Title sort order",
    "XSOP": "Performer sort order",
    "XSOA": "Album sort order",
}

FRAMES_PIPE = [
    UserDefinedTextFrame,
    UserDefinedURLLinkFrame,
    URLLinkFrame,
    PrivateFrame,
    ChapterFrame,
    CommentFrame,
    UFIDFrame,
    AttachedPictureFrame,
    PicardFrame,
    TextFrame,
    MusicMatchMysteryFrame,
    MusicCDIdentifierFrame,
    Frame,
]
