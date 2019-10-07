class Codec:
    ENCODING: str
    SEPARATOR: bytes
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

    def read(self, stream, length=1):
        """Read chars from stream, according to encoding"""
        return stream.read(self.WIDTH * length)

    def decode(self, byte_string):
        """Decode byte_string with given encoding"""
        return byte_string.decode(self.ENCODING)

    def encode(self, byte_string, with_separator=True):
        """Decode byte_string with given encoding"""
        return byte_string.encode(self.ENCODING) + (b'', self.SEPARATOR)[with_separator]

    def __str__(self):
        return self.ENCODING

    def __eq__(self, other):
        return str(self) == str(other)


class Latin1Codec(Codec):
    ENCODING = "latin1"
    SEPARATOR = b'\x00'
    WIDTH = 1


class UTF8Codec(Codec):
    ENCODING = "utf_8"
    SEPARATOR = b'\x00'
    WIDTH = 1


class UTF16BECodec(Codec):
    ENCODING = "utf_16_be"
    SEPARATOR = b'\x00\x00'
    WIDTH = 2


class UTF16Codec(Codec):
    ENCODING = "utf_16"
    SEPARATOR = b'\x00\x00'
    WIDTH = 2


_CODECS = {
    0: Latin1Codec(),
    1: UTF16Codec(),
    2: UTF16BECodec(),
    3: UTF8Codec(),
}
