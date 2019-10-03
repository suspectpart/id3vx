#!/usr/bin/env python3
import sys

from id3vx.tag import Tag, NoTagError, UnsupportedError

if __name__ == "__main__":
    path = sys.argv[1]

    try:
        tag = Tag.from_file(path)
        print(tag, *(repr(frame) for frame in tag), sep="\n")
    except (UnsupportedError, NoTagError) as error:
        print(f"{str(error)} (file: {path})")
        sys.exit(1)
    except Exception as error:
        print(path, file=sys.stderr)
        raise error
