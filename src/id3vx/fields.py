import enum

from id3vx.codec import Codec


class Fields:
    def __init__(self, *args):
        self._fields = args

    def read(self, stream):
        codec = Codec.default()

        results = {}

        for field in self._fields:
            if type(field) == CodecField:
                codec = field.read(stream)
                results[field.name()] = codec
            elif type(field) == EncodedTextField:
                results[field.name()] = field.read(stream, codec)
            else:
                results[field.name()] = field.read(stream)

        return results


class Field:
    def __init__(self, name):
        self._name = name

    def name(self):
        return self._name


class IntegerField(Field):
    def __init__(self, name, length=4):
        super().__init__(name)

        self._length = length

    def read(self, stream) -> int:
        return int.from_bytes(stream.read(self._length), "big")


class EnumField(IntegerField):
    def __init__(self, name, enum_type, length):
        super().__init__(name, length)

        self._enum_type = enum_type

    def read(self, stream) -> enum.Enum:
        return self._enum_type(super().read(stream))


class CodecField(Field):
    def __init__(self):
        super().__init__("codec")

    # noinspection PyMethodMayBeStatic
    def read(self, stream) -> Codec:
        return Codec.get(stream.read(1)[0])


class BinaryField(Field):
    def __init__(self, name, length=-1):
        super().__init__(name)

        self._length = length

    # noinspection PyMethodMayBeStatic
    def read(self, stream) -> bytes:
        return stream.read(self._length)


class TextField(Field):
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


class FixedLengthTextField(Field):
    def __init__(self, name, length):
        super().__init__(name)

        self._length = length

    def read(self, stream) -> str:
        byte_string = Codec.default().read(stream, self._length)

        return Codec.default().decode(byte_string)
