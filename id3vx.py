#!/usr/bin/env python3
from enum import IntFlag
from struct import unpack
import sys

ENCODING = "iso-8859-1"
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

        if not size:
            # considered as padding, throw away
            return None

        return FrameHeader(identifier, size, flags)

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

    def __init__(self, header, fields):
        self._header = header
        self._fields = fields

    def header(self):
        """The header of this frame"""
        return self._header

    def id(self):
        """The 4-letter frame id of this frame.

        See `specification <http://id3.org/id3v2.3.0#Declared_ID3v2_frames>`_
        for a full list.
        """
        return self.header().id().decode(ENCODING)

    def name(self):
        """Human-readable name of a frame.

        Defaults to the 4-letter id if name can not be looked up
        (e.g. when it is a custom extension).
        """
        return DECLARED_FRAMES.get(self.id(), self.id())

    def fields(self):
        """The fields string of this frame"""
        return self._fields.decode(ENCODING)

    def __len__(self):
        """The overall size of the frame in bytes, including header."""
        return FrameHeader.SIZE + self.header().size()

    def __str__(self):
        return f'{self.id()}: {self.fields()}'

    def __repr__(self):
        return f'Frame(' \
               f'{repr(self.header())},' \
               f'fields="{self.fields()}",size={len(self)})'


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
        if identifier.decode(ENCODING) != TagHeader.ID3_IDENTIFIER:
            raise ValueError("No ID3v2.x Tag Header found.")

        self._version = (major, minor)
        self._flags = flags
        self._tag_size = tag_size

    def version(self):
        return self._version

    def tag_size(self):
        """Overall size of the tag, including the header size.

        For convenience reasons, tag size here includes the header size, other
        than the `tag size specification
        <http://id3.org/id3v2.3.0#ID3v2_header>`_ that excludes the header size.
        """
        return len(self) + self._tag_size

    def flags(self):
        return TagHeader.Flags(self._flags)

    def __len__(self):
        """Size of the header. It's 10."""
        return TagHeader.SIZE

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
        """Read ID3v2.3 tag from file"""
        with open(path, 'rb') as mp3:
            header = TagHeader.read_from(mp3)
            frames = []

            while mp3.tell() < header.tag_size():
                frame = Frame.read_from(mp3)

                if not frame:
                    # stop on first padding frame
                    break

                frames.append(frame)

            return Tag(header, frames)

    def header(self):
        """The header of this tag."""
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

    for frame in tag:
        print(repr(frame))
