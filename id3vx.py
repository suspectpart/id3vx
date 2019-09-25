#!/usr/bin/env python3
from enum import IntFlag
from collections import namedtuple
from struct import unpack
import sys


class Frame:
    Header = namedtuple('Header', 'identifier, size, flags')

    class Flags(IntFlag):
        """
        http://id3.org/id3v2.3.0#Frame_header_flags
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
        return self.__payload.decode("iso-8859-1")

    @staticmethod
    def read_from(mp3):
        f_head = Frame.Header(*unpack('>4slh', mp3.read(10)))

        if not f_head.size:
            return None

        return Frame(f_head, mp3.read(f_head.size))

    def __str__(self):
        return f'{self.header().identifier}: {self.payload()}'


class TagHeader:
    """
    Represents the 10-byte ID3v2.x tag header that must be present
    at the very start of a tagged mp3 file.

    See `ID3v2 tag header specification <http://id3.org/id3v2.3.0#ID3v2_header>`
    """

    class Flags(IntFlag):
        Sync = 1 << 6
        Extended = 1 << 5
        Experimental = 1 << 4

    ID3_IDENTIFIER = "ID3"
    SIZE = 10
    Fields = namedtuple('TagHeader', 'identifier, major, minor, flags, tag_size')

    def __init__(self, path_to_mp3):
        with open(path_to_mp3, 'rb') as mp3:
            # TODO: separate tag and tag header
            fields = unpack('>3sBBBl', mp3.read(TagHeader.SIZE))

            self.__fields = TagHeader.Fields(*fields)

            if self._identifier() != TagHeader.ID3_IDENTIFIER:
                raise Exception("No ID3v2.x Tag Header found.")

            self.__frames = []

            while True:
                frame = Frame.read_from(mp3)

                if not frame:
                    break

                self.__frames.append(frame)

    def _flags(self):
        return TagHeader.Flags(self.__fields.flags)

    def _identifier(self):
        return self.__fields.identifier.decode("utf-8")

    def frames(self):
        return self.__frames

    def __repr__(self):
        return repr(self.__fields)


if __name__ == "__main__":
    header = TagHeader(sys.argv[1])

    print(header)

    for frame in header.frames():
        print(frame)
