from id3vx.codec import Codec


class IntegerField:
    def __init__(self, value):
        self._value = value

    def __int__(self):
        return self._value

    @classmethod
    def read(cls, stream, length=4):
        return IntegerField(int.from_bytes(stream.read(length), "big"))


class CodecField:
    @classmethod
    def read(cls, stream):
        return Codec.get(stream.read(1)[0])


class BinaryField(object):
    def __init__(self, byte_string):
        self._bytes = byte_string

    @classmethod
    def read(cls, stream):
        return cls(stream.read())

    def __bytes__(self):
        return self._bytes


class TextField:
    def __init__(self, text):
        self._text = text

    @classmethod
    def read(cls, stream, codec=Codec.default()):
        text_bytes = bytearray()

        char = codec.read(stream)
        while char and (char != codec.SEPARATOR):
            text_bytes += char
            char = codec.read(stream)

        return codec.decode(text_bytes)

    def __str__(self):
        return self._text


class EncodedTextField(TextField):
    @classmethod
    def read(cls, stream, codec=Codec.default()):
        return super().read(stream, codec)


class FixedLengthTextField:
    def __init__(self, text):
        self._text = text

    @classmethod
    def read(cls, stream, length):
        byte_string = Codec.default().read(stream, length)

        return cls(Codec.default().decode(byte_string))

    def __str__(self):
        return self._text
