class Codec:
    def __init__(self, encoding, separator):
        self._encoding = encoding
        self._separator = separator

    @staticmethod
    def default():
        """Default codec specified for id3v2.3 (Latin1 / ISO 8859-1)"""
        return Latin1Codec()

    @staticmethod
    def get(key):
        """Get codec by magic number specified in id3v2.3

        0: Latin1 / ISO 8859-1
        1: UTF-16
        2: UTF-16BE
        3: UTF-8
        """
        return CODECS[key]

    def decode(self, byte_string):
        """Decode byte_string with given encoding"""
        return byte_string.decode(self._encoding)

    def split_decode(self, byte_string: bytes):
        """Split byte_string at separator and decode the parts"""
        parts = self._split(byte_string)

        if (len(parts)) > 1 and not parts[-1]:
            # remove empty trailing string
            parts = parts[:-1]

        return (self.decode(part) for part in parts)

    def _split(self, byte_string):
        return byte_string.rsplit(self._separator)

    def __str__(self):
        return self._encoding


class Latin1Codec(Codec):
    def __init__(self):
        super().__init__("latin1", b'\x00')


class UTF8Codec(Codec):
    def __init__(self):
        super().__init__("utf_8", b'\x00')


class UTF16BECodec(Codec):
    def __init__(self):
        super().__init__("utf_16_be", b'\x00\x00')

    def _split(self, byte_string):
        # utf_16_be means high byte comes first and may be zero
        # so it needs to be split from the left
        return byte_string.split(self._separator)


class UTF16Codec(Codec):
    def __init__(self):
        super().__init__("utf_16", b'\x00\x00')


CODECS = {
    0: Latin1Codec(),
    1: UTF16Codec(),
    2: UTF16BECodec(),
    3: UTF8Codec(),
}
