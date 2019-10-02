#!/usr/bin/env python3
import sys

from id3vx.tag import Tag

if __name__ == "__main__":
    path = sys.argv[1]

    try:
        tag = Tag.read_from(path)
        print(tag, *(repr(frame) for frame in tag), sep="\n")

    except Exception as error:
        print(path, file=sys.stderr)
        raise error
