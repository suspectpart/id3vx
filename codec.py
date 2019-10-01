class Codec:
    encoding: str
    separator: bytes

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

    def decode(self, byte_string):
        """Decode byte_string with given encoding"""
        return byte_string.decode(self.encoding)

    def split_decode(self, byte_string: bytes):
        """Split byte_string at separator and decode the parts"""
        parts = self._split(byte_string)

        if len(parts) > 1 and not parts[-1]:
            parts.pop()  # remove trailing empty string

        return (self.decode(part) for part in parts)

    def _split(self, byte_string):
        return byte_string.split(self.separator)

    def __str__(self):
        return self.encoding

    def __eq__(self, other):
        return str(self) == str(other)


class Latin1Codec(Codec):
    encoding = "latin1"
    separator = b'\x00'


class UTF8Codec(Codec):
    encoding = "utf_8"
    separator = b'\x00'


class UTF16BECodec(Codec):
    encoding = "utf_16_be"
    separator = b'\x00\x00'


class UTF16Codec(Codec):
    encoding = "utf_16"
    separator = b'\x00\x00'

    def _split(self, byte_string):
        # right split because UTF-16LE may cause three successive null bytes
        # e.g. the string "abc" is encoded as b'a\x00b\x00\c\x00\x00\x00'
        return byte_string.rsplit(self.separator)


_CODECS = {
    0: Latin1Codec(),
    1: UTF16Codec(),
    2: UTF16BECodec(),
    3: UTF8Codec(),
}
