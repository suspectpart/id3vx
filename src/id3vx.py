#!/usr/bin/env python3
import sys

from src.tag import Tag

if __name__ == "__main__":
    tag = Tag.read_from(sys.argv[1])

    print(tag)
    print(*(repr(frame) for frame in tag), sep="\n")
    print()
    print(bytes(tag))
