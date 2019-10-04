from id3vx.codec import Codec


class IntegerField:
    def __init__(self, length=4):
        self._length = length

    def read(self, stream) -> int:
        return int.from_bytes(stream.read(self._length), "big")


class CodecField:
    # noinspection PyMethodMayBeStatic
    def read(self, stream) -> Codec:
        return Codec.get(stream.read(1)[0])


class BinaryField(object):
    # noinspection PyMethodMayBeStatic
    def read(self, stream) -> bytes:
        return stream.read()


class TextField:
    def read(self, stream, codec=Codec.default()) -> str:
        text_bytes = b''

        char = codec.read(stream)
        while char and (char != codec.SEPARATOR):
            text_bytes += char
            char = codec.read(stream)

        return codec.decode(text_bytes)


class EncodedTextField(TextField):
    def read(self, stream, codec=Codec.default()) -> str:
        return super().read(stream, codec)


class FixedLengthTextField:
    def __init__(self, length):
        self._length = length

    def read(self, stream) -> str:
        byte_string = Codec.default().read(stream, self._length)

        return Codec.default().decode(byte_string)
