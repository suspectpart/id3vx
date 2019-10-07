import unittest
from io import BytesIO

from id3vx.codec import UTF16Codec, Codec, Latin1Codec, UTF16BECodec, UTF8Codec
from id3vx.fields import EncodedTextField, CodecField, IntegerField, \
    GrowingIntegerField, BinaryField, TextField, FixedLengthTextField, Context


class FixedLengthTextFieldTests(unittest.TestCase):
    def test_read_string_from_stream(self):
        # Arrange
        byte_string = b'hallowelt'
        length = 5

        # System under test
        field = FixedLengthTextField(length)

        # Act
        text = field.read(BytesIO(byte_string), context=None)

        # Assert
        self.assertEqual(text, "hallo")

    def test_read_empty_string_from_stream(self):
        # Arrange
        byte_string = b'hallowelt'

        # System Under Test
        field = FixedLengthTextField(length=0)

        # Act
        text = field.read(BytesIO(byte_string))

        # Assert
        self.assertEqual(text, "")


class CodecFieldTests(unittest.TestCase):
    def test_read_default_codec_from_stream(self):
        """Reads default (Latin1)codec from stream and updates context"""
        # Arrange
        byte_string = b'\x00hallowelt\x00'

        # System under test
        field = CodecField()
        context = Context([field], Latin1Codec())

        # Act
        codec = field.read(BytesIO(byte_string), context)

        # Assert
        self.assertEqual(codec, Codec.default())
        self.assertEqual(context.codec, codec)

    def test_read_utf16_codec_from_stream(self):
        """Reads utf-16 codec from stream and updates context"""
        # Arrange
        byte_string = b'\x01\xff\xfea\x00b\00'

        # System under test
        field = CodecField()
        context = Context([field], Latin1Codec())

        # Act
        codec = field.read(BytesIO(byte_string), context)

        # Assert
        self.assertEqual(type(codec), UTF16Codec)
        self.assertEqual(context.codec, codec)

    def test_read_utf16be_codec_from_stream(self):
        """Reads utf-16-be codec from stream and updates context"""
        # Arrange
        byte_string = b'\x02\xff\xfea\x00b\00'

        # System under test
        field = CodecField()
        context = Context([field], Latin1Codec())

        # Act
        codec = field.read(BytesIO(byte_string), context)

        # Assert
        self.assertEqual(type(codec), UTF16BECodec)
        self.assertEqual(context.codec, codec)

    def test_read_utf8_codec_from_stream(self):
        """Reads utf-8 codec from stream and updates context"""
        # Arrange
        byte_string = b'\x03\xff\xfea\x00b\00'

        # System under test
        field = CodecField()
        context = Context([field], Latin1Codec())

        # Act
        codec = field.read(BytesIO(byte_string), context)

        # Assert
        self.assertEqual(type(codec), UTF8Codec)
        self.assertEqual(context.codec, codec)


class BinaryFieldTests(unittest.TestCase):
    def test_binary_field(self):
        """Greedily reads the full stream"""
        # Arrange
        byte_string = b'abcde\x00\x0f\x00\x0f\x0a\xcf\xff'

        # System under test
        field = BinaryField("text")

        # Act
        field_bytes = field.read(BytesIO(byte_string), context=None)

        # Assert
        self.assertEqual(field_bytes, byte_string)


class TextFieldTests(unittest.TestCase):
    def test_read_delimited_string(self):
        """Reads text up until null terminator \x00"""
        # Arrange
        byte_string = b'abcde\x00'
        remainder = b'\x00\x0f\x00\x0f\x0a\xcf\xff'
        expected_text = "abcde"

        stream = BytesIO(byte_string + remainder)

        # System under test
        field = TextField("text")

        # Act
        text = field.read(stream, context=None)

        # Assert
        self.assertEqual(text, expected_text)
        self.assertEqual(stream.read(), remainder)

    def test_read_undelimited_string(self):
        """Exhausts stream if no delimiter is found"""
        # Arrange
        byte_string = b'abcde\x01\x0f\x02\x0f\x0a\xcf\xff'
        expected_text = byte_string.decode("latin1")

        # System under test - Act
        field = TextField("text").read(BytesIO(byte_string), context=None)

        # Act
        text = str(field)

        # Assert
        self.assertEqual(text, expected_text)

    def test_reads_empty_stream(self):
        """Accepts empty streams"""
        # Arrange
        empty_bytes = b''

        # System under test - Act
        field = TextField("text").read(BytesIO(empty_bytes), context=None)

        # Act
        text = str(field)

        # Assert
        self.assertEqual(text, "")


class EncodedTextFieldTests(unittest.TestCase):
    def test_read_delimited_string(self):
        """Reads text up until null terminator \x00"""
        # Arrange
        context = Context([None], UTF16Codec())
        byte_string = b'\xff\xfea\x00b\x00c\x00d\x00e\x00\x00\x00'
        remainder = b'\xff\xfea\x00b\x00c\x00d\x00e\x00\x00\x00'
        expected_text = "abcde"

        stream = BytesIO(byte_string + remainder)

        # System under test - Act
        field = EncodedTextField("text").read(stream, context)

        # Act
        text = str(field)

        # Assert
        self.assertEqual(text, expected_text)
        self.assertEqual(stream.read(), remainder)

    def test_read_undelimited_string(self):
        """Exhausts stream if no delimiter is found"""
        # Arrange
        context = Context([None], UTF16Codec())
        byte_string = b'\xff\xfea\x00b\x00c\x00d\x00e\x00'
        expected_text = "abcde"

        # System under test - Act
        field = EncodedTextField("text").read(BytesIO(byte_string), context=context)

        # Act
        text = str(field)

        # Assert
        self.assertEqual(text, expected_text)

    def test_reads_empty_stream(self):
        """Accepts empty streams"""
        # Arrange
        empty_bytes = b''
        context = Context([None], UTF16Codec())

        # System under test
        field = EncodedTextField("text")

        # Act
        text = field.read(BytesIO(empty_bytes), context)

        # Assert
        self.assertEqual(text, "")


class GrowingIntegerFieldTests(unittest.TestCase):
    def test_reads_many_bytes(self):
        """Reads all bytes"""
        # Arrange
        byte_string = b'\x00\x00\xff\xff\xff\xff\x00\x00'
        expected_int = 0xffffffff0000

        stream = BytesIO(byte_string)

        # System under test
        field = GrowingIntegerField()

        # Act
        value = field.read(stream, context=None)

        # Assert
        self.assertEqual(value, expected_int)

    def test_reads_zero_byte_int(self):
        """Reads some bytes"""
        # Arrange
        byte_string = b''
        expected_int = 0

        stream = BytesIO(byte_string)

        # System under test
        field = GrowingIntegerField()

        # Act
        value = field.read(stream, context=None)

        # Assert
        self.assertEqual(value, expected_int)

    def test_reads_single_byte_int(self):
        """Reads a single byte as int"""
        # Arrange
        byte_string = b'\xff'
        expected_int = 0xff

        stream = BytesIO(byte_string)

        # System under test
        field = GrowingIntegerField()

        # Act
        value = field.read(stream, context=None)

        # Assert
        self.assertEqual(value, expected_int)


class IntegerFieldTests(unittest.TestCase):
    def test_reads_four_byte_int(self):
        """Reads 4 byte integer from stream"""
        # Arrange
        byte_string = b'\x00\x00\xff\xff'
        remainder = b'\xff\xff\x00\x00'
        expected_int = 0xffff

        stream = BytesIO(byte_string + remainder)

        # System under test
        field = IntegerField("field")

        # Act
        value = field.read(stream, context=None)

        # Assert
        self.assertEqual(value, expected_int)
        self.assertEqual(stream.read(), remainder)

    def test_reads_n_byte_int(self):
        """Reads a zero from empty stream"""
        # Arrange
        byte_string = b'\xff\xee\xcc\xdd'
        expected_int = 0xffeecc

        stream = BytesIO(byte_string)

        # System under test
        field = IntegerField("field", 3)

        # Act
        value = field.read(stream, context=None)

        # Assert
        self.assertEqual(value, expected_int)

    def test_reads_single_byte_int(self):
        """Reads a zero from empty stream"""
        # Arrange
        byte_string = b'\xff\xee\xcc\xdd'
        expected_int = 0xff

        stream = BytesIO(byte_string)

        # System under test
        field = IntegerField("field", 1).read(stream, context=None)

        # Act
        value = int(field)

        # Assert
        self.assertEqual(value, expected_int)

    def test_reads_empty_stream(self):
        """Reads a zero from empty stream"""
        # Arrange
        byte_string = b''
        stream = BytesIO(byte_string)

        # System under test - Act
        field = IntegerField("field").read(stream, context=None)

        # Act
        value = int(field)

        # Assert
        self.assertEqual(value, 0)
