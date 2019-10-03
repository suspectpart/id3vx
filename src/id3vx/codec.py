class Codec:
    ENCODING: str
    separator: bytes
    WIDTH: int

    @staticmethod
    def default():
        """Default codec specified for id3v2.3 (Latin1 / ISO 8859-1)"""
        return _CODECS.get(0)

    @staticmethod
    def get(key):
        """Get codec by magic number specified in id3v2.3

        0: Latin1 / ISO 8859-1
        1: UTF-16
        2: UTF-16BE
        3: UTF-8
        """
        return _CODECS[key]

    def read(self, stream):
        return stream.read(self.WIDTH)

    def decode(self, byte_string):
        """Decode byte_string with given encoding"""
        return byte_string.decode(self.ENCODING)

    def encode(self, byte_string):
        """Decode byte_string with given encoding"""
        return byte_string.encode(self.ENCODING) + self.separator

    def split(self, byte_string, maxsplit=None):
        """Splits a string at separator"""
        return byte_string.split(self.separator, maxsplit or -1)

    def split_decode(self, byte_string: bytes, tokens=None):
        """Split byte_string at separator and decode the parts"""
        parts = self.split(byte_string)[:tokens]
        return (self.decode(part) for part in parts)

    def __str__(self):
        return self.ENCODING

    def __eq__(self, other):
        return str(self) == str(other)


class Latin1Codec(Codec):
    ENCODING = "latin1"
    separator = b'\x00'
    WIDTH = 1


class UTF8Codec(Codec):
    ENCODING = "utf_8"
    separator = b'\x00'
    WIDTH = 1


class UTF16BECodec(Codec):
    ENCODING = "utf_16_be"
    separator = b'\x00\x00'
    WIDTH = 2


class UTF16Codec(Codec):
    ENCODING = "utf_16"
    separator = b'\x00\x00'
    WIDTH = 2

    def split(self, byte_string, maxsplit=None):
        # rsplit because UTF-16LE can cause three successive null bytes
        # e.g. "abc" is encoded as b'a\x00b\x00\c\x00\x00\x00'
        parts = byte_string.rsplit(self.separator)

        if not maxsplit:
            return parts

        # pick maxsplit parts and join the rest back together
        return [*parts[:maxsplit], self.separator.join(parts[maxsplit:])]


_CODECS = {
    0: Latin1Codec(),
    1: UTF16Codec(),
    2: UTF16BECodec(),
    3: UTF8Codec(),
}
