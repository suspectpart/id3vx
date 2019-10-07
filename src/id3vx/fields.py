import enum
from dataclasses import Field, MISSING

from id3vx.binary import unsynchsafe, synchsafe
from id3vx.codec import Codec, _CODECS


class Context:
    """Stateful context to be handed down the fields pipeline.

    Some fields down the pipe need to know whether there as an encoding
    field present or if they are the last field in the pipe.
    """
    def __init__(self, fields, codec=Codec.default(), synchsafe_size=False):
        self.codec = codec
        self.last = fields[-1]
        self.synchsafe_size = synchsafe_size


class BaseField(Field):
    def __init__(self, default=MISSING):
        super().__init__(default=default, default_factory=MISSING, init=True, repr=True, hash=None, compare=True,
                         metadata=None)

#    @abstractmethod
    def read(self, stream, context):
        ...


class IntegerField(BaseField):
    def __init__(self, default=0, length=4):
        """Field reading single integers from a byte stream.

        :param length: The number of bytes of the integer (defaults to 4)
        """
        super().__init__(default)

        self._length = length

    def read(self, stream, context) -> int:
        """Reads a single integer from the stream

        :param stream: The stream to read from
        :param context: State of the fields pipeline
        :return: An integer
        """
        return int.from_bytes(stream.read(self._length), "big")


class GrowingIntegerField(IntegerField):
    """Field that reads all bytes from a byte stream, interpreted as int.

    (as if that made any sense at all.)
    """
    def __init__(self):
        super().__init__(length=-1)


class SynchsafeIntegerField(IntegerField):
    def read(self, stream, context) -> int:
        return unsynchsafe(super().read(stream, context))


class EnumField(IntegerField):
    def __init__(self, enum_type, length):
        """Field reading a single int, converting to an enum type.

        :param enum_type: The enum type to convert to
        :param length: Number of bytes of the enum integer
        """
        super().__init__(length=length)

        self._enum_type = enum_type

    def read(self, stream, context=None) -> enum.Enum:
        return self._enum_type(super().read(stream, context))

    def write(self, stream, value, context):
        stream.write(int(value).to_bytes(self._length, "big"))


class CodecField(BaseField):
    def __init__(self):
        super().__init__(Codec.default())

    def read(self, stream, context) -> Codec:
        codec = Codec.get(stream.read(1)[0])
        context.codec = codec

        return codec

    def write(self, stream, value: Codec, context):
        context.codec = value
        codec_key = list(_CODECS.keys())[list(_CODECS.values()).index(value.ENCODING)]

        stream.write(codec_key.to_bytes(1, "big"))


class BinaryField(BaseField):
    def __init__(self, default=b'', length=-1):
        super().__init__(default)

        self._length = length

    def read(self, stream, context) -> bytes:
        return stream.read(self._length)

    def write(self, stream, value, context) -> bytes:
        stream.write(value)


class TextField(BaseField):
    def __init__(self, default=""):
        super().__init__(default)

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

    def write(self, stream, value: str, context):
        stream.write(Codec.default().encode(value, context.last != self))


class EncodedTextField(TextField):
    def read(self, stream, context) -> str:
        return super()._read(stream, context.codec)

    def write(self, stream, value, context):
        encoded = context.codec.encode(value, self != context.last)

        stream.write(encoded)


class FixedLengthTextField(BaseField):
    def __init__(self, length):
        super().__init__("")

        self._length = length
        self._codec = Codec.default()

    def read(self, stream, context=None) -> str:
        byte_string = self._codec.read(stream, self._length)

        return self._codec.decode(byte_string)

    def write(self, stream, value, context):
        stream.write(self._codec.encode(value, False))


class SynchsafeHackField(IntegerField):
    """You know what it is"""
    def read(self, stream, context):
        value = super().read(stream, context)
        return unsynchsafe(value) if context.synchsafe_size else value

    def write(self, stream, value: int, context):
        value = value.to_bytes(4, "big")
        stream.write(synchsafe(value) if context.synchsafe_size else value)


class NoopField(BaseField):
    def __init__(self, default):
        super().__init__(default)

    def read(self, stream, context) -> None:
        return None

    def write(self, stream, value, context):
        pass
