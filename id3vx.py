#!/usr/bin/env python3
from enum import IntFlag
from struct import unpack
import sys

DEFAULT_ENCODING = "iso-8859-1"
ENCODINGS = {
    0: "iso-8859-1",
    # TODO: I just guessed this, this won't work for sure
    1: "utf_16",
    2: "utf_16_be",
    3: "utf-8",
}

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
    "UFID": "1 Unique file identifier",
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
}


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

        TagAlterPreservation = 1 << 14
        FileAlterPreservation = 1 << 13
        ReadOnly = 1 << 12
        Compression = 1 << 7
        Encryption = 1 << 6
        GroupingIdentity = 1 << 5

    @staticmethod
    def read_from(mp3):
        identifier, size, flags = unpack('>4slh', mp3.read(10))
        return FrameHeader(identifier, size, flags) if size else None

    def __init__(self, identifier, size, flags):
        self._id = identifier
        self._size = size
        self._flags = flags

    def flags(self):
        return FrameHeader.Flags(self._flags)

    def id(self):
        return self._id

    def size(self):
        """The size specified in the header, excluding the header size itself"""
        return self._size

    def frame_type(self):
        # TODO: this might be own class FrameId that handles this magic
        if self.id().startswith(b"T"):
            return TextFrame
        elif self.id() == b"WXXX":
            return UserDefinedURLLinkFrame
        elif self.id() == b'COMM':
            return CommentFrame

        return Frame

    def __repr__(self):
        return f'FrameHeader(id={self.id()},' \
               f'size={self.size()},' \
               f'flags={str(self.flags())})'


class Frame:
    """An ID3v2.3 frame.

    Refer to `ID3v2.3 frame specification
    <http://id3.org/id3v2.3.0#ID3v2_frame_overview>`_
    """

    @staticmethod
    def read_from(mp3):
        """Read the next frame from an mp3 file object"""
        header = FrameHeader.read_from(mp3)
        return Frame(header, mp3.read(header.size())) if header else None

    def __new__(cls, *args, **kwargs):
        """Create instance of Frame subclass depending on the type"""
        return super().__new__(args[0].frame_type())

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
        return self.header().id().decode(DEFAULT_ENCODING)

    def name(self):
        """Human-readable name of a frame.

        Defaults to the 4-letter id if name can not be looked up
        (e.g. when it is a custom extension).
        """
        return DECLARED_FRAMES.get(self.id(), self.id())

    def __len__(self):
        """The overall size of the frame in bytes, including header."""
        return FrameHeader.SIZE + self.header().size()

    def __str__(self):
        return str(self.fields())

    def __repr__(self):
        return f'{type(self).__name__}(' \
               f'{repr(self.header())},' \
               f'fields="{str(self)}",size={len(self)})'


class TextFrame(Frame):
    """A text frame

    Decodes all of the frame with the encoding read from the first byte.
    """
    def text(self):
        return super().fields()[1:].decode(self.encoding())

    def encoding(self):
        return ENCODINGS.get(super().fields()[0], DEFAULT_ENCODING)

    def separator(self):
        return b"\x00\x00" if self.encoding().startswith("utf_16") else b"\x00"

    def __str__(self):
        return self.text()


class UserDefinedURLLinkFrame(TextFrame):
    """A User Defined URL Frame

    Reads comment and description from an already decoded TextFrame.
    """
    def __init__(self, header, fields):
        super().__init__(header, fields)
        description, url = super().fields()[1:].split(self.separator(), 1)

        self._description = description
        self._url = url

    def description(self):
        return self._description.decode(self.encoding())

    def url(self):
        return self._url.decode(DEFAULT_ENCODING)

    def __str__(self):
        return f'[description {self.description()}] {self.url()}'


class CommentFrame(TextFrame):
    """Comment Frame

    Reads language, description and comment from an already decoded TextFrame.
    """
    def __init__(self, header, fields):
        super().__init__(header, fields)

        self._language = fields[1:4]
        self._description, self._comment = fields[4:].split(self.separator(), 1)

    def language(self):
        return self._language.decode(DEFAULT_ENCODING)

    def description(self):
        return self._description.decode(self.encoding())

    def comment(self):
        return self._comment.decode(self.encoding())

    def __str__(self):
        return f'[language {self.language()}]' \
               f'[description {self.description()}] ' \
               f'{self.comment()}'


class TagHeader:
    """ID3v2.3 tag header.

    Represents the 10-byte ID3v2.3 tag header that must be present
    at the very start of a tagged mp3 file, prefixed with the magic
    file signature "TAG".

    See `ID3v2 tag header specification
    <http://id3.org/id3v2.3.0#ID3v2_header>`_
    """
    ID3_IDENTIFIER = "ID3"
    SIZE = 10

    class Flags(IntFlag):
        """
        Represents the 1-byte tag flags.

        See `ID3v2.3 tag header specification
        <http://id3.org/id3v2.3.0#ID3v2_header>`_
        """
        Sync = 1 << 6
        Extended = 1 << 5
        Experimental = 1 << 4

    @staticmethod
    def read_from(mp3):
        return TagHeader(*unpack('>3sBBBl', mp3.read(TagHeader.SIZE)))

    def __init__(self, identifier, major, minor, flags, tag_size):
        if identifier.decode(DEFAULT_ENCODING) != TagHeader.ID3_IDENTIFIER:
            raise ValueError("No ID3v2.x Tag Header found.")

        self._version = (major, minor)
        self._flags = flags
        self._tag_size = tag_size

    def version(self):
        return self._version

    def flags(self):
        return TagHeader.Flags(self._flags)

    def tag_size(self):
        """Overall size of the tag, including the header size.

        For convenience reasons, tag size here includes the header size, other
        than the `tag size specification
        <http://id3.org/id3v2.3.0#ID3v2_header>`_ that excludes the header size.
        """
        return TagHeader.SIZE + self._tag_size

    def __repr__(self):
        major, minor = self.version()

        return f"TagHeader(major={major},minor={minor}," \
               f"flags={self.flags()},tag_size={self._tag_size})"


class Tag:
    """An ID3v2.3 tag.

    Represents a full ID3v2.3 tag, consisting of a header and a list of frames.

    See `ID3v2.3 tag specification
    <http://id3.org/id3v2.3.0#ID3v2_overview>`_
    """

    def __init__(self, header, frames):
        self._header = header
        self._frames = frames

    @staticmethod
    def read_from(path):
        """Read full ID3v2.3 tag from mp3 file"""
        with open(path, 'rb') as mp3:
            header = TagHeader.read_from(mp3)
            frames = Tag._read_frames_from(mp3, header)

            return Tag(header, frames)

    @staticmethod
    def _read_frames_from(mp3, header):
        """Read frames from mp3 file

        Read consecutive frames up until tag size specified in the header.
        Stops reading frames when an empty (padding) frame is encountered.
        """
        frames = []

        while mp3.tell() < header.tag_size():
            frame = Frame.read_from(mp3)

            if frame:
                frames.append(frame)
            else:
                # stop on first padding frame
                break

        return frames

    def header(self):
        return self._header

    def __iter__(self):
        return iter(self._frames)

    def __len__(self):
        """The overall size of the tag in bytes, including header."""
        return self.header().tag_size()

    def __repr__(self):
        return f"Tag({repr(self.header())},size={len(self)})"


if __name__ == "__main__":
    path_to_mp3 = sys.argv[1]
    tag = Tag.read_from(path_to_mp3)

    print(tag)
    print(*(repr(frame) for frame in tag), sep="\n")
