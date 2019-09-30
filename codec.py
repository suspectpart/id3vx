class Codec:
    SEPARATOR = b'\x00'
    ENCODINGS = {
        0: "latin_1",
        1: "utf_16",
        2: "utf_16_be",
        3: "utf-8",
    }

    def __init__(self, byte=0):
        self._codec = Codec.ENCODINGS[byte]

    def separator(self):
        if self._codec.startswith("utf_16"):
            return Codec.SEPARATOR * 2
        return Codec.SEPARATOR

    @staticmethod
    def default():
        return Codec()

    def decode(self, byte_string):
        return byte_string.decode(self._codec)

    def split(self, byte_string: bytes):
        """Split and decode a string at the null byte \x00

        If encoding is utf_16, two null bytes \x00\x00 are removed.
        """

        if self._codec != 'utf_16_be':
            parts = byte_string.rsplit(self.separator())
        else:
            parts = byte_string.split(self.separator())

        if (len(parts)) > 1 and not parts[-1]:
            parts = parts[:-1]

        return (self.decode(part) for part in parts)

    def __str__(self):
        return self._codec
