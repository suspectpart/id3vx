#!/usr/bin/env python3
from struct import unpack
from collections import namedtuple
import sys

ID3_MAGIC_IDENTIFIER = "ID3"

TagHeader = namedtuple('TagHeader', 'identifier, major, minor, flags, size')

if __name__ == "__main__":
    path_to_mp3 = sys.argv[1]

    with open(path_to_mp3, 'rb') as mp3:
        first_block = mp3.read(10)
        tag_header = TagHeader._make(unpack('>3sBBBl', first_block))

        if tag_header.identifier.decode("utf-8") != ID3_MAGIC_IDENTIFIER:
            raise Exception("No id3v2.x Tag Header found.")

        print(tag_header)
