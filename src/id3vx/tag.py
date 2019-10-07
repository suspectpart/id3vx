import dataclasses
import struct
from dataclasses import dataclass
from enum import IntFlag

from id3vx.binary import synchsafe
from id3vx.fields import FixedLengthTextField, IntegerField, \
    EnumField, SynchsafeIntegerField, Context
from .frame import Frames


class NoTagError(Exception):
    def __init__(self):
        super().__init__("No ID3v2.x Tag Header found.")


class UnsupportedError(NotImplementedError):
    def __init__(self, message):
        super().__init__(message)


@dataclass
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

    identifier: str = FixedLengthTextField(3)
    major: int = IntegerField(length=1)
    minor: int = IntegerField(length=1)
    flags: Flags = EnumField(Flags, 1)
    tag_size: int = SynchsafeIntegerField()

    @classmethod
    def read(cls, mp3):
        fields = dataclasses.fields(cls)
        context = Context(fields)

        return cls(**{f.name: f.read(mp3, context) for f in fields})

    def __post_init__(self):
        if self.identifier != TagHeader.ID3_IDENTIFIER:
            raise NoTagError()

        if self.major < 3:
            # FIXME: v2.2 is completely broken due to shorter Frame IDs
            msg = f"ID3v2.{self.major}.{self.minor} is not supported"
            raise UnsupportedError(msg)

        if TagHeader.Flags.Sync in self.flags:
            # FIXME: v2.4 reads out of bounds on unsynchronisation frames
            raise UnsupportedError(f"Unsynchronisation is not supported")

    def __bytes__(self):
        return struct.pack('>3sBBBL',
                           bytes(TagHeader.ID3_IDENTIFIER, "latin1"),
                           self.major,
                           self.minor,
                           self.flags,
                           synchsafe(self.tag_size))

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
    def from_file(cls, path):
        """Read full ID3v2.3 tag from mp3 file"""
        with open(path, 'rb') as mp3:
            header = TagHeader.read(mp3)
            frames = Frames.read(mp3, header)

        return cls(header, frames)

    def header(self):
        return self._header

    def __iter__(self):
        return self._frames.__iter__()

    def __len__(self):
        """The overall size of the tag in bytes, including header."""
        return self.header().tag_size + len(self.header())

    def __repr__(self):
        return f"Tag({repr(self.header())},size={len(self)})"

    def __bytes__(self):
        header = bytes(self.header())
        frames = b"".join(bytes(frame) for frame in self)

        return header + frames
