import unittest

from id3vx.text import shorten


class TextTests(unittest.TestCase):
    def test_shorten_text(self):
        # Arrange
        text = "01234567890"
#
        # Act
        shortened = shorten(text, 100)

        # Assert
        self.assertEqual(shortened, text)

    def test_shorten_long_text(self):
        # Arrange
        text = "01234567890"
        expected = "01234 ..."

        # Act
        shortened = shorten(text, 5)

        # Assert
        self.assertEqual(shortened, expected)
