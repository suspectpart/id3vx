#!/usr/bin/env python3
from enum import IntFlag
from struct import unpack
import sys

ENCODING = "iso-8859-1"


class FrameHeader:
    """A single 10-byte ID3v2.3 frame header.

    Refer to `ID3v2.3 specification
    <http://id3.org/id3v2.3.0#ID3v2_frame_overview>`_
    """

    class Flags(IntFlag):
        """Represents 2-byte flags of the frame header.

         Refer to `ID3v2.3 specification
        <http://id3.org/id3v2.3.0#Frame_header_flags>`_
        """
        TagAlterPreservation = 1 << 14
        FileAlterPreservation = 1 << 13
        ReadOnly = 1 << 12
        Compression = 1 << 7
        Encryption = 1 << 6
        GroupingIdentity = 1 << 5

    def __init__(self, identifier, size, flags):
        self._id = identifier
        self._size = size
        self._flags = flags

    @staticmethod
    def read_from(mp3):
        identifier, size, flags = unpack('>4slh', mp3.read(10))

        if not size:
            # must be padding
            return None

        return FrameHeader(identifier, size, flags)

    def flags(self):
        return FrameHeader.Flags(self._flags)

    def id(self):
        return self._id

    def frame_size(self):
        return self._size

    def __repr__(self):
        return f'FrameHeader(id={self.id()},' \
               f'size={self.frame_size()},' \
               f'flags={str(self.flags())})'


class Frame:
    """An ID3v2.3 frame.

    See also `frame specification
    <http://id3.org/id3v2.3.0#ID3v2_frame_overview>`_
    """

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

    def fields(self):
        """The fields string of this frame"""

        return self._fields.decode(ENCODING)

    @staticmethod
    def read_from(mp3):
        header = FrameHeader.read_from(mp3)

        if not header:
            return None

        return Frame(header, mp3.read(header.frame_size()))

    def __str__(self):
        return f'{self.header().identifier()}: {self.fields()}'

    def __repr__(self):
        return f'Frame(' \
               f'{repr(self.header())},' \
               f'fields="{self.fields()}")'


class TagHeader:
    """ID3v2.3 tag header.

    Represents the 10-byte ID3v2.3 tag header that must be present
    at the very start of a tagged mp3 file, prefixed with the magic
    file signature "TAG".

    See `ID3v2 tag header specification
    <http://id3.org/id3v2.3.0#ID3v2_header>`_
    """

    class Flags(IntFlag):
        """
        Represents the 1-byte tag flags.

        See `ID3v2.3 tag header specification
        <http://id3.org/id3v2.3.0#ID3v2_header>`_
        """
        Sync = 1 << 6
        Extended = 1 << 5
        Experimental = 1 << 4

    ID3_IDENTIFIER = "ID3"
    SIZE = 10

    def __init__(self, identifier, major, minor, flags, tag_size):
        if identifier.decode(ENCODING) != TagHeader.ID3_IDENTIFIER:
            raise ValueError("No ID3v2.x Tag Header found.")

        self._version = (major, minor)
        self._flags = flags
        self._tag_size = tag_size

    def version(self):
        return self._version

    def tag_size(self):
        return self._tag_size

    def flags(self):
        return TagHeader.Flags(self._flags)

    def __len__(self):
        """Size of the header. It's 10."""

        return TagHeader.SIZE

    @staticmethod
    def read_from(mp3):
        return TagHeader(*unpack('>3sBBBl', mp3.read(TagHeader.SIZE)))

    def __repr__(self):
        major, minor = self.version()

        return f"TagHeader(major={major},minor={minor}," \
               f"flags={self.flags()},tag_size={self.tag_size()})"


class Tag:
    """An ID3v2.3 tag.

    Represents a full ID3v2.3 tag, consisting of a header and a list of frames.

    See `ID3v2.3 tag header specification
    <http://id3.org/id3v2.3.0#ID3v2_overview>`_
    """

    def __init__(self, path_to_mp3):
        with open(path_to_mp3, 'rb') as mp3:
            self._header = TagHeader.read_from(mp3)
            self._frames = []

            while mp3.tell() < len(self):
                frame = Frame.read_from(mp3)

                if frame:
                    self._frames.append(frame)
                else:
                    # stop if padding is encountered (empty frames)
                    break

    def header(self):
        """The header of this tag."""

        return self._header

    def frames(self):
        """A list of all frames in this tag."""

        return self._frames

    def __len__(self):
        """The overall size of the tag in bytes."""

        return len(self.header()) + self.header().tag_size()

    def __repr__(self):
        return f"Tag({repr(self.header())}, size={len(self)})"


if __name__ == "__main__":
    tag = Tag(sys.argv[1])
    print(tag)

    for f in tag.frames():
        print(repr(f))
