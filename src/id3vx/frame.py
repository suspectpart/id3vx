import datetime
import enum
import inspect
import struct
import sys
from collections import namedtuple
from enum import IntFlag
from io import BytesIO

from id3vx.binary import unsynchsafe
from id3vx.fields import TextField, BinaryField, FixedLengthTextField
from id3vx.fields import CodecField, EncodedTextField, IntegerField
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

        frame_id = header.id().decode("latin1")
        frame = FRAMES.get(frame_id, Frame)

        return frame(header, fields)

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

    @staticmethod
    def represents(identifier):
        return identifier == b'APIC'

    def __init__(self, header, fields):
        super().__init__(header, fields)

        # There are some tags that contain only three null bytes \x00\x00\x00
        # right before the data starts. Parsing them causes all the fields
        # to be slightly off, e.g. the JPEG header slips into the description,
        # reading ÿØÿà. kid3 and eyeD3 Have the same issue, so that seems to
        # be a violation of the spec and it's not just me being stupid.
        with BytesIO(fields) as stream:
            self._codec = CodecField.read(stream)
            self._mime_type = TextField.read(stream)
            self._picture_type = IntegerField.read(stream, 1)
            self._description = EncodedTextField.read(stream, self._codec)
            self._data = BinaryField.read(stream)

    def picture_type(self):
        return self.PictureType(int(self._picture_type))

    def description(self):
        return str(self._description)

    def mime_type(self):
        return str(self._mime_type)

    def data(self):
        return bytes(self._data)

    def __str__(self):
        return f"[mime-type={self.mime_type()}]" \
               f"[description={self.description()}]" \
               f"[picture-type={self.picture_type()}]" \
               f"[data={self.data()}]"


class MCDI(Frame):
    """A Music CD Identifier Frame (MCDI)

    <Header for 'Music CD identifier', ID: "MCDI">
    CD TOC <binary data>

    See `specification <http://id3.org/id3v2.3.0#Music_CD_identifier>`_
    """

    @staticmethod
    def represents(identifier):
        return identifier == b'MCDI'

    def toc(self):
        return self.fields()


class NCON(Frame):
    """A mysterious binary frame added by MusicMatch (NCON)"""

    @staticmethod
    def represents(identifier):
        return identifier == b'NCON'


class PRIV(Frame):
    """Private frame (PRIV)

    <Header for 'Private frame', ID: "PRIV">
    Owner identifier        <text string> $00
    The private data        <binary data>

    See `specification <http://id3.org/id3v2.3.0#Private_frame>`_
    """

    def __init__(self, header, fields):
        super().__init__(header, fields)

        with BytesIO(fields) as stream:
            self._owner = TextField.read(stream)
            self._data = BinaryField.read(stream)

    @staticmethod
    def represents(identifier):
        return identifier == b'PRIV'

    def owner(self):
        return str(self._owner)

    def data(self):
        return bytes(self._data)

    def __str__(self):
        return f'[owner {self.owner()}] {self.data()}'


class UFID(PRIV):
    """Unique file identifier frame (UFID)

    <Header for 'Unique file identifier', ID: "UFID">
    Owner identifier    <text string> $00
    Identifier          <up to 64 bytes binary data>

    See `specification <http://id3.org/id3v2.3.0#Unique_file_identifier>`_
    """

    @staticmethod
    def represents(identifier):
        return identifier == b'UFID'


class TextFrame(Frame):
    """A text information frame (T000 - TZZZ)

    <Header for 'Text information frame', ID: "T000" - "TZZZ",
    excluding "TXXX" described in 4.2.2.>
    Text encoding   $xx
    Information     <text string according to encoding>

    See `specification <http://id3.org/id3v2.3.0#Text_information_frames>`_
    """

    def __init__(self, header, fields):
        super().__init__(header, fields)

        with BytesIO(fields) as stream:
            self._codec = CodecField.read(stream)
            self._text = EncodedTextField.read(stream, codec=self._codec)

    @staticmethod
    def represents(identifier):
        return identifier.startswith(b'T')

    def text(self):
        return str(self._text)

    def __str__(self):
        return self.text()


class PicardFrame(TextFrame):
    """A Special, kind of hacky frame introduced by MusicBrainz Picard (XSO*)

    Can be XSOA, XSOT or XSOP that map to TSOA, TSOT and TSOP in ID3v2.4
    """

    @staticmethod
    def represents(identifier):
        return identifier in [b'XSOA', b'XSOP', b'XSOT']


class XSOP(PicardFrame):
    """Performing Artist sort order"""


class XSOA(PicardFrame):
    """Album sort order"""


class XSOT(PicardFrame):
    """Track sort oder"""


class TXXX(Frame):
    """User defined text information frame (TXXX)

    <Header for 'User defined text information frame', ID: "TXXX">
    Text encoding   $xx
    Description     <text string according to encoding> $00 (00)
    Value           <text string according to encoding>

    See `specification
    <http://id3.org/id3v2.3.0#User_defined_text_information_frame>`_
    """

    def __init__(self, header, fields):
        super().__init__(header, fields)

        with BytesIO(fields) as stream:
            self._codec = CodecField.read(stream)
            self._description = EncodedTextField.read(stream, self._codec)
            self._text = EncodedTextField.read(stream, self._codec)

    @staticmethod
    def represents(identifier):
        return identifier == b'TXXX'

    def text(self):
        return str(self._text)

    def description(self):
        return str(self._description)

    def __str__(self):
        return f'[description {self.description()}] {self.text()}'


class URLLinkFrame(Frame):
    """Url link Frame (W000 - WZZZ)

    <Header for 'URL link frame', ID: "W000" - "WZZZ",
    excluding "WXXX" described in 4.3.2.>
    URL <text string>

    See `specification <http://id3.org/id3v2.3.0#URL_link_frames>`_
    """

    def url(self):
        return Codec.default().decode(self.fields())

    def __str__(self):
        return self.url()

    @staticmethod
    def represents(identifier):
        return identifier == b'WOAR'


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


class WXXX(Frame):
    """A User Defined URL Frame (WXXX)

    <Header for 'User defined URL link frame', ID: "WXXX">
    Text encoding    $xx
    Description     <text string according to encoding> $00 (00)
    URL             <text string>

    See `specification
    <http://id3.org/id3v2.3.0#User_defined_URL_link_frame>`_
    """

    def __init__(self, header, fields):
        super().__init__(header, fields)

        with BytesIO(fields) as stream:
            self._codec = CodecField.read(stream)
            self._description = EncodedTextField.read(stream, self._codec)
            self._url = TextField.read(stream)

    @staticmethod
    def represents(identifier):
        return identifier == b'WXXX'

    def description(self):
        return str(self._description)

    def url(self):
        return str(self._url)

    def __str__(self):
        return f'[description {self.description()}] {self.url()}'


class COMM(Frame):
    """Comment Frame (COMM)

    <Header for 'Comment', ID: "COMM">
    Text encoding              $xx
    Language                   $xx xx xx
    Short content descrip.     <text string according to encoding> $00 (00)
    The actual text            <full text string according to encoding>

    See `specification <http://id3.org/id3v2.3.0#Comments>`_
    """

    def __init__(self, header, fields):
        super().__init__(header, fields)

        with BytesIO(fields) as stream:
            self._codec = CodecField.read(stream)
            self._language = FixedLengthTextField.read(stream, 3)
            self._description = EncodedTextField.read(stream, self._codec)
            self._comment = EncodedTextField.read(stream, self._codec)

    @staticmethod
    def represents(identifier):
        return identifier == b'COMM'

    def language(self):
        return str(self._language)

    def description(self):
        return str(self._description)

    def comment(self):
        return str(self._comment)

    def __str__(self):
        return f'[language {self.language()}]' \
               f'[description {self.description()}] ' \
               f'{self.comment()}'


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

    Timings = namedtuple("Timings", "start, end, start_offset, end_offset")

    def __init__(self, header, fields):
        super().__init__(header, fields)

        with BytesIO(fields) as stream:
            self._element_id = TextField.read(stream)
            self._start_time = IntegerField.read(stream)
            self._end_time = IntegerField.read(stream)
            self._start_offset = IntegerField.read(stream)
            self._end_offset = IntegerField.read(stream)
            # TODO: needs to be another field
            self._sub_frames = stream.read()

    @staticmethod
    def represents(identifier):
        return identifier == b'CHAP'

    def sub_frames(self):
        """CHAP frames include 0-2 sub frames (of type TIT2 and TIT3)"""
        with BytesIO(self._sub_frames) as io:
            frames = [Frame.from_file(io), Frame.from_file(io)]

        return (f for f in frames if f)

    def element_id(self):
        return str(self._element_id)

    def start(self):
        return datetime.timedelta(milliseconds=int(self._start_time))

    def end(self):
        return datetime.timedelta(milliseconds=int(self._end_time))

    def offset_start(self):
        return int(self._start_offset)

    def offset_end(self):
        return int(self._end_offset)

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
        timings = struct.pack('>LLLL',
                              int(self._start_time),
                              int(self._end_time),
                              self.offset_start(),
                              self.offset_end())

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


class TALB(TextFrame):
    """Album/Movie/Show title"""


class TBPM(TextFrame):
    """BPM' frame contains the number of beats per minute in the mainpart
    of the audio. The BPM is an integer and represented as a numerical string.
    """


class TCOM(TextFrame):
    """The 'Composer(s)' frame is intended for the name of the composer(s).
    They are seperated with the "/" character.
    """


class TCON(TextFrame):
    """The 'Content type', which previously was stored as a one byte numeric
    value only, is now a numeric string. You may use one or several of the
    types as ID3v1.1 did or, since the category list would be impossible to
    maintain with accurate and up to date categories, define your own.
    """


class TCOP(TextFrame):
    """The 'Copyright message' frame, which must begin with a year and a space
    character (making five characters), is intended for the copyright holder
    of the original sound, not the audio file itself. The absence of this
    frame means only that the copyright information is unavailable or has been
    removed, and must not be interpreted to mean that the sound is public
    domain. Every time this field is displayed the field must be
    preceded with "Copyright © ".
    """


class TDAT(TextFrame):
    """The 'Date' frame is a numeric string in the DDMM format containing the
    date for the recording. This field is always four characters long.
    """


class TDLY(TextFrame):
    """The 'Playlist delay' defines the numbers of milliseconds of silence
    between every song in a playlist. The player should use the "ETC" frame, if
    present, to skip initial silence and silence at the end of the audio to
    match the 'Playlist delay' time. The time is represented as a numeric
    string.
    """


class TENC(TextFrame):
    """The 'Encoded by' frame contains the name of the person or organisation
    that encoded the audio file. This field may contain a copyright message,
    if the audio file also is copyrighted by the encoder.
    """


class TEXT(TextFrame):
    """The 'Lyricist(s)/Text writer(s)' frame is intended for the writer(s) of
    the text or lyrics in the recording.
    They are seperated with the "/" character.
    """


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
    """'Interpreted, remixed, or otherwise modified by"""


class TPOS(TextFrame):
    """'Part of a set'"""


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


classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)
FRAMES = {name: clazz for (name, clazz) in classes}
