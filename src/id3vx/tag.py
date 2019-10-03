import struct
from enum import IntFlag

from id3vx.binary import unsynchsafe, synchsafe
from .codec import Codec
from .frame import Frame


class NoTagError(Exception):
    def __init__(self):
        super().__init__("No ID3v2.x Tag Header found.")


class UnsupportedError(NotImplementedError):
    def __init__(self, message):
        super().__init__(message)


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
        Sync = 1 << 7
        Extended = 1 << 6
        Experimental = 1 << 5
        FooterPresent = 1 << 4

    @classmethod
    def read_from(cls, mp3):
        block = mp3.read(TagHeader.SIZE)
        identifier, major, minor, flags, size = struct.unpack('>3sBBBL', block)

        flags = TagHeader.Flags(flags)
        size = unsynchsafe(size)

        return cls(identifier, major, minor, flags, size)

    def __init__(self, identifier, major, minor, flags, tag_size):
        if Codec.default().decode(identifier) != TagHeader.ID3_IDENTIFIER:
            raise NoTagError()

        if major < 3:
            # FIXME: v2.2 is completely broken due to shorter Frame IDs
            raise UnsupportedError(f"ID3v2.{major}.{minor} is not supported")

        if TagHeader.Flags.Sync in flags:
            # FIXME: v2.4 reads out of bounds on unsynchronisation frames
            raise UnsupportedError(f"Unsynchronisation is not supported")

        self._version = (major, minor)
        self._flags = flags
        self._tag_size = tag_size

    def version(self):
        return self._version

    def flags(self):
        return self._flags

    def tag_size(self):
        """Overall size of the tag, including the header size.

        For convenience reasons, tag size here includes the header size, other
        than the `tag size specification
        <http://id3.org/id3v2.3.0#ID3v2_header>`_ that excludes the header size
        """
        return self._tag_size

    def __repr__(self):
        major, minor = self.version()

        return f"TagHeader(major={major},minor={minor}," \
            f"flags={str(self.flags())},tag_size={self._tag_size})"

    def __bytes__(self):
        return struct.pack('>3sBBBL',
                           bytes(TagHeader.ID3_IDENTIFIER, "latin1"),
                           *self.version(),
                           self.flags(),
                           synchsafe(self.tag_size()))

    def __len__(self):
        return TagHeader.SIZE


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
        unsynchronize_frame_size = header.version()[0] == 4
        frames = []

        while mp3.tell() < header.tag_size():
            frame = Frame.read_from(mp3, unsynchronize_frame_size)

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
        return self.header().tag_size() + len(self.header())

    def __repr__(self):
        return f"Tag({repr(self.header())},size={len(self)})"

    def __bytes__(self):
        header = bytes(self.header())
        frames = b"".join(bytes(frame) for frame in self)
        padding = self.header().tag_size() - len(frames)

        return header + frames + b'\x00' * padding
