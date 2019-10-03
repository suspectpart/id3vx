import unittest
from io import BytesIO

from id3vx.codec import UTF16Codec, Codec
from id3vx.fields import BinaryField, TextField
from id3vx.fields import EncodedTextField, CodecField, IntegerField


class CodecFieldTests(unittest.TestCase):
    def test_read_default_codec_from_stream(self):
        # Arrange
        byte_string = b'\x00hallowelt\x00'

        # Act
        codec = CodecField.read(BytesIO(byte_string))

        # Assert
        self.assertEqual(codec, Codec.default())

    def test_read_utf16_codec_from_stream(self):
        # Arrange
        byte_string = b'\x01\xff\xfea\x00b\00'

        # Act
        codec = CodecField.read(BytesIO(byte_string))

        # Assert
        self.assertEqual(codec, Codec.get(1))

    def test_read_utf16be_codec_from_stream(self):
        # Arrange
        byte_string = b'\x02\xff\xfea\x00b\00'

        # Act
        codec = CodecField.read(BytesIO(byte_string))

        # Assert
        self.assertEqual(codec, Codec.get(2))

    def test_read_utf8_codec_from_stream(self):
        # Arrange
        byte_string = b'\x02\xff\xfea\x00b\00'

        # Act
        codec = CodecField.read(BytesIO(byte_string))

        # Assert
        self.assertEqual(codec, Codec.get(2))


class BinaryFieldTests(unittest.TestCase):
    def test_binary_field(self):
        """Greedily reads the full stream"""
        # Arrange
        byte_string = b'abcde\x00\x0f\x00\x0f\x0a\xcf\xff'

        # System under test - Act
        field = BinaryField.read(BytesIO(byte_string))

        # Act
        field_bytes = bytes(field)

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

        # System under test - Act
        field = TextField.read(stream)

        # Act
        text = str(field)

        # Assert
        self.assertEqual(text, expected_text)
        self.assertEqual(stream.read(), remainder)

    def test_read_undelimited_string(self):
        """Exhausts stream if no delimiter is found"""
        # Arrange
        byte_string = b'abcde\x01\x0f\x02\x0f\x0a\xcf\xff'
        expected_text = byte_string.decode("latin1")

        # System under test - Act
        field = TextField.read(BytesIO(byte_string))

        # Act
        text = str(field)

        # Assert
        self.assertEqual(text, expected_text)

    def test_reads_empty_stream(self):
        """Accepts empty streams"""
        # Arrange
        empty_bytes = b''

        # System under test - Act
        field = TextField.read(BytesIO(empty_bytes))

        # Act
        text = str(field)

        # Assert
        self.assertEqual(text, "")


class EncodedTextFieldTests(unittest.TestCase):
    def test_read_delimited_string(self):
        """Reads text up until null terminator \x00"""
        # Arrange
        byte_string = b'\xff\xfea\x00b\x00c\x00d\x00e\x00\x00\x00'
        remainder = b'\xff\xfea\x00b\x00c\x00d\x00e\x00\x00\x00'
        expected_text = "abcde"

        stream = BytesIO(byte_string + remainder)

        # System under test - Act
        field = EncodedTextField.read(stream, UTF16Codec())

        # Act
        text = str(field)

        # Assert
        self.assertEqual(text, expected_text)
        self.assertEqual(stream.read(), remainder)

    def test_read_undelimited_string(self):
        """Exhausts stream if no delimiter is found"""
        # Arrange
        codec = UTF16Codec()
        byte_string = b'\xff\xfea\x00b\x00c\x00d\x00e\x00'
        expected_text = "abcde"

        # System under test - Act
        field = EncodedTextField.read(BytesIO(byte_string), codec)

        # Act
        text = str(field)

        # Assert
        self.assertEqual(text, expected_text)

    def test_reads_empty_stream(self):
        """Accepts empty streams"""
        # Arrange
        empty_bytes = b''

        # System under test - Act
        field = EncodedTextField.read(BytesIO(empty_bytes), UTF16Codec())

        # Act
        text = str(field)

        # Assert
        self.assertEqual(text, "")


class IntegerFieldTests(unittest.TestCase):
    def test_reads_four_byte_int(self):
        """Reads 4 byte integer from stream"""
        # Arrange
        byte_string = b'\x00\x00\xff\xff'
        remainder = b'\xff\xff\x00\x00'
        expected_int = 0xffff

        stream = BytesIO(byte_string + remainder)

        # System under test - Act
        field = IntegerField.read(stream)

        # Act
        value = int(field)

        # Assert
        self.assertEqual(value, expected_int)
        self.assertEqual(stream.read(), remainder)

    def test_reads_n_byte_int(self):
        """Reads a zero from empty stream"""
        # Arrange
        byte_string = b'\xff\xee\xcc\xdd'
        expected_int = 0xffeecc

        stream = BytesIO(byte_string)

        # System under test - Act
        field = IntegerField.read(stream, length=3)

        # Act
        value = int(field)

        # Assert
        self.assertEqual(value, expected_int)

    def test_reads_single_byte_int(self):
        """Reads a zero from empty stream"""
        # Arrange
        byte_string = b'\xff\xee\xcc\xdd'
        expected_int = 0xff

        stream = BytesIO(byte_string)

        # System under test - Act
        field = IntegerField.read(stream, length=1)

        # Act
        value = int(field)

        # Assert
        self.assertEqual(value, expected_int)

    def test_reads_empty_stream(self):
        """Reads a zero from empty stream"""
        # Arrange
        byte_string = b''
        expected_int = 0

        stream = BytesIO(byte_string)

        # System under test - Act
        field = IntegerField.read(stream)

        # Act
        value = int(field)

        # Assert
        self.assertEqual(value, expected_int)
