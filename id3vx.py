#!/usr/bin/env python3
from enum import IntFlag
from collections import namedtuple
from struct import unpack
import sys

ENCODING = "iso-8859-1"


class Frame:
    """
    Represents a single 10-byte ID3v2.3 frame.

    Refer to `ID3v2.3 specification
    <http://id3.org/id3v2.3.0#ID3v2_frame_overview>`_
    """
    Header = namedtuple('Header', 'identifier, size, flags')

    class Flags(IntFlag):
        """
        Represents 2-byte flags included in a frame header.

         Refer to `ID3v2.3 specification
        <http://id3.org/id3v2.3.0#Frame_header_flags>`_
        """
        TagAlterPreservation = 1 << 14
        FileAlterPreservation = 1 << 13
        ReadOnly = 1 << 12
        Compression = 1 << 7
        Encryption = 1 << 6
        GroupingIdentity = 1 << 5

    def __init__(self, header, payload):
        self.__header = header
        self.__payload = payload

    def header(self):
        return self.__header

    def payload(self):
        return self.__payload.decode(ENCODING)

    @staticmethod
    def read_from(mp3):
        f_head = Frame.Header(*unpack('>4slh', mp3.read(10)))

        if not f_head.size:
            return None

        return Frame(f_head, mp3.read(f_head.size))

    def __str__(self):
        return f'{self.header().identifier}: {self.payload()}'


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
    Fields = namedtuple('TagHeader',
                        'identifier, major, minor, flags, tag_size')

    def __init__(self, fields):
        self.__fields = fields

        if self.identifier() != TagHeader.ID3_IDENTIFIER:
            raise ValueError("No ID3v2.x Tag Header found.")

    def __len__(self):
        """Size of the header. It's 10."""

        return TagHeader.SIZE

    def identifier(self):
        return self.__fields.identifier.decode(ENCODING)

    @staticmethod
    def read_from(mp3):
        block = unpack('>3sBBBl', mp3.read(TagHeader.SIZE))

        return TagHeader(TagHeader.Fields(*block))

    def __repr__(self):
        return repr(self.__fields)


class Tag:

    class Flags(IntFlag):
        """
        Represents the 1-byte header flags.

        See `ID3v2.3 tag header specification
        http://id3.org/id3v2.3.0#ID3v2_header`_
        """
        Sync = 1 << 6
        Extended = 1 << 5
        Experimental = 1 << 4

    def __init__(self, path_to_mp3):
        with open(path_to_mp3, 'rb') as mp3:
            self.__header = TagHeader.read_from(mp3)
            self.__frames = []

            while True:
                frame = Frame.read_from(mp3)

                if not frame:
                    break

                self.__frames.append(frame)

    def header(self):
        return self.__header

    def frames(self):
        return self.__frames

    def __repr__(self):
        return repr(self.header())


if __name__ == "__main__":
    tag = Tag(sys.argv[1])

    print(tag)

    for frame in tag.frames():
        print(frame)
