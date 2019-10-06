import enum
from abc import ABC, abstractmethod

from id3vx.codec import Codec


class Fields:
    class Context:
        """Stateful context to be handed down the fields pipeline.

        Some fields down the pipe need to know whether there as an encoding
        field present or if they are the last field in the pipe.
        """
        def __init__(self, fields, codec=Codec.default()):
            self.codec = codec
            self.last = fields[:-1]

    def __init__(self, *args):
        self._fields = args

    def read(self, stream):
        context = Fields.Context(self._fields)
        results = {}

        for field in self._fields:
            results[field.name()] = field.read(stream, context)

        return results


class Field(ABC):
    def __init__(self, name):
        self._name = name

    def name(self):
        return self._name

    @abstractmethod
    def read(self, stream, context):
        ...


class IntegerField(Field):
    def __init__(self, name, length=4):
        super().__init__(name)

        self._length = length

    def read(self, stream, context=None) -> int:
        return int.from_bytes(stream.read(self._length), "big")


class GrowingIntegerField(IntegerField):
    """Reads all bytes in the stream and interprets them as int

    (as if that made any sense at all.)
    """
    def __init__(self, name):
        super().__init__(name, -1)


class EnumField(IntegerField):
    def __init__(self, name, enum_type, length):
        super().__init__(name, length)

        self._enum_type = enum_type

    def read(self, stream, context=None) -> enum.Enum:
        return self._enum_type(super().read(stream, context))


class CodecField(Field):
    def __init__(self):
        super().__init__("codec")

    def read(self, stream, context) -> Codec:
        codec = Codec.get(stream.read(1)[0])
        context.codec = codec

        return codec


class BinaryField(Field):
    def __init__(self, name, length=-1):
        super().__init__(name)

        self._length = length

    def read(self, stream, context) -> bytes:
        return stream.read(self._length)


class TextField(Field):
    def read(self, stream, context) -> str:
        return self._read(stream, Codec.default())

    # noinspection PyMethodMayBeStatic
    def _read(self, stream, codec):
        text_bytes = b''

        char = codec.read(stream)
        while char and (char != codec.SEPARATOR):
            text_bytes += char
            char = codec.read(stream)

        return codec.decode(text_bytes)


class EncodedTextField(TextField):
    def read(self, stream, context) -> str:
        return super()._read(stream, context.codec)


class FixedLengthTextField(Field):
    def __init__(self, name, length):
        super().__init__(name)

        self._length = length

    def read(self, stream, context=None) -> str:
        byte_string = Codec.default().read(stream, self._length)

        return Codec.default().decode(byte_string)
