import datetime
import enum
import inspect
import struct
import sys
from dataclasses import dataclass
from enum import IntFlag
from io import BytesIO

from id3vx.binary import unsynchsafe
from id3vx.fields import TextField, BinaryField, FixedLengthTextField, Fields
from id3vx.fields import CodecField, EncodedTextField, IntegerField, EnumField
from .codec import Codec
from .text import shorten


class Frames(list):
    """Represents a all Frames in a Tag."""

    @classmethod
    def read(cls, stream, header):
        """Reads all frames from a stream

        Read consecutive frames up until tag size specified in the header.
        Stops reading frames when an empty (padding) frame is encountered.
        """
        synchsafe_frame_size = header.version()[0] == 4
        frames = []

        while stream.tell() < header.tag_size():
            frame = Frame.read(stream, synchsafe_frame_size)

            if not frame:
                # stop on first padding frame
                break

            frames.append(frame)

        return cls(frames)

    def __init__(self, args):
        super().__init__(args)


@dataclass
class FrameHeader:
    """A single 10-byte ID3v2.3 frame header.

    Refer to `ID3v2.3 frame header specification
    <http://id3.org/id3v2.3.0#ID3v2_frame_overview>`_
    """
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

    FIELDS = Fields(
        FixedLengthTextField("identifier", 4),
        IntegerField("frame_size", 4),
        EnumField("flags", Flags, 2)
    )

    SIZE = 10

    identifier: str
    frame_size: int
    flags: Flags
    synchsafe_size: bool

    @classmethod
    def read(cls, stream, synchsafe_size=False):
        return cls(**cls.FIELDS.read(stream), synchsafe_size=synchsafe_size)

    def __post_init__(self):
        # Still hacky...
        if self.synchsafe_size:
            self.frame_size = unsynchsafe(self.frame_size)

    def __bytes__(self):
        return struct.pack('>4sLH',
                           self.identifier.encode("latin1"),
                           self.frame_size,
                           self.flags)

    def __repr__(self):
        return f"FrameHeader({self.identifier}," \
               f"frame_size={self.frame_size}," \
               f"flags={str(self.flags)}" \
               f"{['',',synchsafe'][self.synchsafe_size]}"

    def __bool__(self):
        return self.frame_size > 0

    def __len__(self):
        return FrameHeader.SIZE


@dataclass(repr=False)
class Frame:
    """An ID3v2.3 frame.

    Refer to `ID3v2.3 frame specification
    <http://id3.org/id3v2.3.0#ID3v2_frame_overview>`_
    """
    header: FrameHeader
    fields: bytes

    FIELDS = Fields()

    @classmethod
    def read(cls, stream, synchsafe_size=False):
        """Reads a single frame from a stream"""
        header = FrameHeader.read(stream, synchsafe_size)

        if not header:
            return None

        frame_bytes = stream.read(header.frame_size)
        frame_class = FRAMES.get(header.identifier, Frame)

        return frame_class.create_from(header, frame_bytes)

    @classmethod
    def create_from(cls, header, frame_bytes):
        """Creates a new Frame from header and frame_bytes"""
        with BytesIO(frame_bytes) as stream:
            fields = cls.FIELDS.read(stream)

        # noinspection PyArgumentList
        return cls(header, frame_bytes, **fields)

    def id(self):
        """The 4-letter frame id of this frame.

        See `specification <http://id3.org/id3v2.3.0#Declared_ID3v2_frames>`_
        for a full list.
        """
        return self.header.identifier

    def __len__(self):
        """The overall size of the frame in bytes, including header."""
        return len(self.header) + self.header.frame_size

    def __repr__(self):
        fields = self.__annotations__
        values = ((f, shorten(str(self.__dict__[f]))) for f in fields)
        attrs = "".join(f"[{k}={v}]" for k, v in values)

        return f'{type(self).__name__}({repr(self.header)}) {attrs}'

    def __bytes__(self):
        return bytes(self.header) + bytes(self.fields)


@dataclass(repr=False)
class APIC(Frame):
    """Attached picture frame (APIC)

    <Header for 'Attached picture', ID: "APIC">
    Text encoding   $xx
    MIME type       <text string> $00
    Picture type    $xx
    Description     <text string according to encoding> $00 (00)
    Picture data    <binary data>

    See `specification <http://id3.org/id3v2.3.0#Attached_picture>`_
    """
    class PictureType(enum.Enum):
        OTHER = 0x00  # "Other"
        ICON = 0x01  # "32x32 pixels 'file icon' (PNG only)"
        OTHER_ICON = 0x02  # "Other file icon"
        FRONT_COVER = 0x03  # "Cover (front)"
        BACK_COVER = 0x04  # "Cover (back)"
        LEAFLET = 0x05  # "Leaflet page"
        MEDIA = 0x06  # "Media (e.g. lable side of CD)"
        LEAD_ARTIST = 0x07  # "Lead artist/lead performer/soloist"
        ARTIST = 0x08  # "Artist/performer"
        CONDUCTOR = 0x09  # "Conductor"
        BAND = 0x0A  # "Band/Orchestra"
        COMPOSER = 0x0B  # "Composer"
        LYRICIST = 0x0C  # "Lyricist/text writer"
        RECORD_LOCATION = 0x0D  # "Recording Location"
        DURING_LOCATION = 0x0E  # "During recording"
        DURING_PERFORMANCE = 0x0F  # "During performance"
        SCREEN_CAPTURE = 0x10  # "Movie/video screen capture"
        BRIGHT_COLORED_FISH = 0x11  # "A bright coloured fish"
        ILLUSTRATION = 0x12  # "Illustration"
        BAND_LOGO_TYPE = 0x13  # "Band/artist logotype"
        PUBLISHER_LOGO_TYPE = 0x14  # "Publisher/Studio logotype"

    codec: Codec
    mime_type: str
    picture_type: PictureType
    description: str
    data: bytes

    FIELDS = Fields(
        CodecField(),
        TextField("mime_type"),
        EnumField("picture_type", PictureType, 1),
        EncodedTextField("description"),
        BinaryField("data"),
    )


@dataclass(repr=False)
class MCDI(Frame):
    """A Music CD Identifier Frame (MCDI)

    <Header for 'Music CD identifier', ID: "MCDI">
    CD TOC <binary data>

    See `specification <http://id3.org/id3v2.3.0#Music_CD_identifier>`_
    """
    toc: bytes

    FIELDS = Fields(
        BinaryField("toc"),
    )


@dataclass(repr=False)
class PRIV(Frame):
    """Private frame (PRIV)

    <Header for 'Private frame', ID: "PRIV">
    Owner identifier        <text string> $00
    The private data        <binary data>

    See `specification <http://id3.org/id3v2.3.0#Private_frame>`_
    """
    owner: str
    data: bytes

    FIELDS = Fields(
        TextField("owner"),
        BinaryField("data")
    )


@dataclass(repr=False)
class GEOB(Frame):
    """General encapsulated object (GEOB)

    <Header for 'General encapsulated object', ID: "GEOB">
    Text encoding           $xx
    MIME type               <text string> $00
    Filename                <text string according to encoding> $00 (00)
    Content description     $00 (00)
    Encapsulated object     <binary data>

    See `specification <http://id3.org/id3v2.3.0#General_encapsulated_object>`_
    """
    codec: Codec
    mime_type: str
    filename: str
    description: str
    obj: str

    FIELDS = Fields(
        CodecField(),
        TextField("mime_type"),
        EncodedTextField("filename"),
        EncodedTextField("description"),
        BinaryField("obj"),
    )


@dataclass(repr=False)
class TextFrame(Frame):
    """A text information frame (T000 - TZZZ)

    <Header for 'Text information frame', ID: "T000" - "TZZZ",
    excluding "TXXX" described in 4.2.2.>
    Text encoding   $xx
    Information     <text string according to encoding>

    See `specification <http://id3.org/id3v2.3.0#Text_information_frames>`_
    """
    codec: Codec
    text: str

    FIELDS = Fields(
        CodecField(),
        EncodedTextField("text"),
    )


@dataclass(repr=False)
class TXXX(Frame):
    """User defined text information frame (TXXX)

    <Header for 'User defined text information frame', ID: "TXXX">
    Text encoding   $xx
    Description     <text string according to encoding> $00 (00)
    Value           <text string according to encoding>

    See `specification
    <http://id3.org/id3v2.3.0#User_defined_text_information_frame>`_
    """
    codec: Codec
    description: str
    text: str

    FIELDS = Fields(
        CodecField(),
        EncodedTextField("description"),
        EncodedTextField("text"),
    )


@dataclass(repr=False)
class URLLinkFrame(Frame):
    """Url link Frame (W000 - WZZZ)

    <Header for 'URL link frame', ID: "W000" - "WZZZ",
    excluding "WXXX" described in 4.3.2.>
    URL <text string>

    See `specification <http://id3.org/id3v2.3.0#URL_link_frames>`_
    """
    url: str

    FIELDS = Fields(
        TextField("url"),
    )


@dataclass(repr=False)
class WXXX(Frame):
    """A User Defined URL Frame (WXXX)

    <Header for 'User defined URL link frame', ID: "WXXX">
    Text encoding    $xx
    Description     <text string according to encoding> $00 (00)
    URL             <text string>

    See `specification
    <http://id3.org/id3v2.3.0#User_defined_URL_link_frame>`_
    """
    codec: Codec
    description: str
    url: str

    FIELDS = Fields(
        CodecField(),
        EncodedTextField("description"),
        TextField("url"),
    )


@dataclass(repr=False)
class COMM(Frame):
    """Comment Frame (COMM)

    <Header for 'Comment', ID: "COMM">
    Text encoding              $xx
    Language                   $xx xx xx
    Short content descrip.     <text string according to encoding> $00 (00)
    The actual text            <full text string according to encoding>

    See `specification <http://id3.org/id3v2.3.0#Comments>`_
    """
    codec: Codec
    language: str
    description: str
    comment: str

    FIELDS = Fields(
        CodecField(),
        FixedLengthTextField("language", 3),
        EncodedTextField("description"),
        EncodedTextField("comment"),
    )


@dataclass(repr=False)
class PCNT(Frame):
    """Play counter (PCNT)

    <Header for 'Play counter', ID: "PCNT">
    Counter        $xx xx xx xx (xx ...)

    See `specification <http://id3.org/id3v2.3.0#Play_counter>`_
    """
    counter: int

    # FIXME: doesn't (but who listens to a song more than 2 ** 32 - 1 times?)
    FIELDS = Fields(
        IntegerField("counter")
    )


@dataclass(repr=False)
class USLT(Frame):
    """Unsynchronised lyrics (USLT)

    <Header for 'Unsynchronised lyrics/text transcription', ID: "USLT">
    Text encoding       $xx
    Language            $xx xx xx
    Content descriptor  <text string according to encoding> $00 (00)
    Lyrics/text         <full text string according to encoding>
    """
    codec: Codec
    language: str
    description: str
    lyrics: str

    FIELDS = Fields(
        CodecField(),
        FixedLengthTextField("language", 3),
        EncodedTextField("description"),
        EncodedTextField("lyrics"),
    )


@dataclass(repr=False)
class CHAP(Frame):
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
    element_id: str
    start_time: int
    end_time: int
    start_offset: int
    end_offset: int
    _sub_frames: bytes

    FIELDS = Fields(
        TextField("element_id"),
        IntegerField("start_time"),
        IntegerField("end_time"),
        IntegerField("start_offset"),
        IntegerField("end_offset"),
        BinaryField("_sub_frames"),
    )

    def sub_frames(self):
        """CHAP frames include 0-2 sub frames (of type TIT2 and TIT3)"""
        with BytesIO(self._sub_frames) as io:
            frames = [Frame.read(io), Frame.read(io)]

        return (f for f in frames if f)

    def __repr__(self):
        start = datetime.timedelta(milliseconds=self.start_time)
        end = datetime.timedelta(milliseconds=self.end_time)

        return f'{super().__repr__()}' \
               f'[element_id={self.element_id}]' \
               f'[start={start}]' \
               f'[end={end}]' \
               f'[start_offset={self.start_offset}]' \
               f'[end_offset={self.end_offset}]' \
               f'[sub_frames={" ".join(repr(f) for f in self.sub_frames())}]'

    def __bytes__(self):
        header = bytes(self.header)
        element_id = Codec.default().encode(self.element_id)
        timings = struct.pack('>LLLL',
                              int(self.start_time),
                              int(self.end_time),
                              self.start_offset,
                              self.end_offset)

        return header + element_id + timings + self._sub_frames


@dataclass(repr=False)
class USER(Frame):
    """Terms of use (USER)

    <Header for 'Terms of use frame', ID: "USER">
    Text encoding   $xx
    Language        $xx xx xx
    The actual text <text string according to encoding>
    """
    codec: Codec
    language: str
    text: str

    FIELDS = Fields(
        CodecField(),
        FixedLengthTextField("language", 3),
        EncodedTextField("text"),
    )


class TALB(TextFrame):
    """Album/Movie/Show title"""


class TCMP(TextFrame):
    """Part of a compilation (iTunes)"""


class TBPM(TextFrame):
    """BPM"""


class TCOM(TextFrame):
    """Composer(s)"""


class TCON(TextFrame):
    """Content type"""


class TCOP(TextFrame):
    """Copyright message"""


class TDAT(TextFrame):
    """Date"""


class TDRC(TextFrame):
    """Recording time"""


class TDLY(TextFrame):
    """Playlist delay"""


class TENC(TextFrame):
    """Encoded by"""


class TENB(TextFrame):
    """Encoded by (???). Found with iTunes tagged mp3s."""


class TEXT(TextFrame):
    """Lyricist(s)/Text writer(s)"""


class TFLT(TextFrame):
    """The 'File type' frame indicates which type of audio this tag defines."""


class TIME(TextFrame):
    """Time"""


class TIT1(TextFrame):
    """Content group description"""


class TIT2(TextFrame):
    """Title/Songname/Content description"""


class TIT3(TextFrame):
    """Subtitle/Description refinement"""


class TKEY(TextFrame):
    """Initial key"""


class TLAN(TextFrame):
    """Language(s)"""


class TLEN(TextFrame):
    """Length"""


class TMED(TextFrame):
    """Media type"""


class TOAL(TextFrame):
    """Original album/movie/show title"""


class TOFN(TextFrame):
    """Original filename"""


class TOLY(TextFrame):
    """Original lyricist(s)/text writer(s)"""


class TOPE(TextFrame):
    """Original artist(s)/performer(s)"""


class TORY(TextFrame):
    """Original release year"""


class TOWN(TextFrame):
    """File owner/licensee"""


class TPE1(TextFrame):
    """Lead artist(s)/Lead performer(s)/Soloist(s)/Performing group"""


class TPE2(TextFrame):
    """Band/Orchestra/Accompaniment"""


class TPE3(TextFrame):
    """Conductor"""


class TPE4(TextFrame):
    """Interpreted, remixed, or otherwise modified by"""


class TPOS(TextFrame):
    """Part of a set"""


class TPRO(TextFrame):
    """Produced notice"""


class TPUB(TextFrame):
    """Publisher"""


class TRCK(TextFrame):
    """Track number/Position in set"""


class TRDA(TextFrame):
    """Recording dates"""


class TRSN(TextFrame):
    """Internet radio station name"""


class TRSO(TextFrame):
    """Internet radio station owner"""


class TSIZ(TextFrame):
    """Size"""


class TSRC(TextFrame):
    """ISRC (International Standard Recording Code) (12 characters)"""


class TSSE(TextFrame):
    """Software/Hardware and settings used for encoding"""


class TYER(TextFrame):
    """Year (4 characters)"""


class WCOM(URLLinkFrame):
    """Commercial information"""


class WCOP(URLLinkFrame):
    """Copyright/Legal information"""


class WOAF(URLLinkFrame):
    """Official audio file webpage"""


class WOAR(URLLinkFrame):
    """Official artist/performer webpage"""


class WOAS(URLLinkFrame):
    """Official audio source webpage"""


class WORS(URLLinkFrame):
    """Official internet radio station homepage"""


class WPAY(URLLinkFrame):
    """Payment"""


class WPUB(URLLinkFrame):
    """Publishers official webpage"""


class NCON(Frame):
    """A mysterious binary frame added by MusicMatch (NCON)"""


class PicardFrame(TextFrame):
    """Mysterious frame introduced by MusicBrainz Picard (XSO*)"""


class XSOP(PicardFrame):
    """MusicBrainz Performing Artist sort order"""


class XSOA(PicardFrame):
    """MusicBrainz Album sort order"""


class XSOT(PicardFrame):
    """MusicBrainz Track sort oder"""


class UFID(PRIV):
    """Unique file identifier frame (UFID)

    <Header for 'Unique file identifier', ID: "UFID">
    Owner identifier    <text string> $00
    Identifier          <up to 64 bytes binary data>

    See `specification <http://id3.org/id3v2.3.0#Unique_file_identifier>`_
    """


# Is this good practice? I don't know...
classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)
FRAMES = {name: clazz for (name, clazz) in classes}
