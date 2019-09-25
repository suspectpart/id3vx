#!/usr/bin/env python3
from struct import unpack
from collections import namedtuple
import sys


class TagHeader:
    """
    Represents the 10-byte ID3v2.x tag header that must be present
    at the very start of a tagged mp3 file.

    See `ID3v2 tag header specification <http://id3.org/id3v2.3.0#ID3v2_header>`
    """

    ID3_IDENTIFIER = "ID3"
    Fields = namedtuple('TagHeader', 'identifier, major, minor, flags, size')

    def __init__(self, path_to_mp3):
        with open(path_to_mp3, 'rb') as mp3:
            fields = unpack('>3sBBBl', mp3.read(10))
            self.__header = TagHeader.Fields(*fields)

        if self._identifier() != TagHeader.ID3_IDENTIFIER:
            raise Exception("No ID3v2.x Tag Header found.")

    def _identifier(self):
        return self.__header.identifier.decode("utf-8")

    def __repr__(self):
        return repr(self.__header)


if __name__ == "__main__":
    print(TagHeader(sys.argv[1]))
