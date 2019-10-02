import struct
from enum import IntFlag

from .codec import Codec
from .frame import Frame


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

    @classmethod
    def read_from(cls, mp3):
        return cls(*struct.unpack('>3sBBBL', mp3.read(TagHeader.SIZE)))

    def __init__(self, identifier, major, minor, flags, tag_size):
        if Codec.default().decode(identifier) != TagHeader.ID3_IDENTIFIER:
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
        <http://id3.org/id3v2.3.0#ID3v2_header>`_ that excludes the header size
        """
        return TagHeader.SIZE + self._tag_size

    def __repr__(self):
        major, minor = self.version()

        return f"TagHeader(major={major},minor={minor}," \
            f"flags={self.flags()},tag_size={self._tag_size})"

    def __bytes__(self):
        return struct.pack('>3sBBBL',
                           bytes(TagHeader.ID3_IDENTIFIER, "latin1"),
                           *self.version(),
                           self.flags(),
                           self.tag_size() - TagHeader.SIZE)


class Tag:
    """An ID3v2.3 tag.

    Represents a full ID3v2.3 tag, consisting of a header and a list of frames.

    See `ID3v2.3 tag specification
    <http://id3.org/id3v2.3.0#ID3v2_overview>`_
    """

    def __init__(self, header, frames):
        self._header = header
        self._frames = frames

    @classmethod
    def read_from(cls, path):
        """Read full ID3v2.3 tag from mp3 file"""
        with open(path, 'rb') as mp3:
            header = TagHeader.read_from(mp3)
            frames = Tag._read_frames_from(mp3, header)

        return cls(header, frames)

    @staticmethod
    def _read_frames_from(mp3, header):
        """Read frames from mp3 file

        Read consecutive frames up until tag size specified in the header.
        Stops reading frames when an empty (padding) frame is encountered.
        """
        frames = []

        while mp3.tell() < header.tag_size():
            frame = Frame.read_from(mp3)

            if not frame:
                # stop on first padding frame
                break

            frames.append(frame)

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

    def __bytes__(self):
        header = bytes(self.header())
        frames = b"".join(bytes(frame) for frame in self)
        padding = self.header().tag_size() - len(frames)

        return header + frames + b'\x00' * padding
