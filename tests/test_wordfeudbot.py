import wordfeudbot.main as wfbot
import unittest


class TestStringMethods(unittest.TestCase):

    def test_is_emoji(self):
        self.assertTrue(wfbot.is_emoji('😁'))
        self.assertTrue(wfbot.is_emoji('😂'))
        self.assertTrue(wfbot.is_emoji('🤣'))
        self.assertTrue(wfbot.is_emoji('😃'))
        self.assertTrue(wfbot.is_emoji('😄'))
        self.assertTrue(wfbot.is_emoji('👩'))
        self.assertTrue(wfbot.is_emoji('👨'))
        self.assertTrue(wfbot.is_emoji('🧑🏿'))
        self.assertTrue(wfbot.is_emoji('🎈'))
        self.assertTrue(wfbot.is_emoji('🎆'))
        self.assertTrue(wfbot.is_emoji('🍋'))
        self.assertTrue(wfbot.is_emoji('🛹'))
        self.assertTrue(wfbot.is_emoji('⚡'))
        self.assertTrue(wfbot.is_emoji('💟'))
        self.assertTrue(wfbot.is_emoji('⏪'))
        self.assertTrue(wfbot.is_emoji('🕕'))
        self.assertTrue(wfbot.is_emoji('😃🕕🍋'))
        self.assertTrue(wfbot.is_emoji('👨🛹'))
        self.assertTrue(wfbot.is_emoji('🎆😃💟💟💟⏪'))
        self.assertFalse(wfbot.is_emoji('a'))
        self.assertFalse(wfbot.is_emoji('b'))
        self.assertFalse(wfbot.is_emoji('c'))
        self.assertFalse(wfbot.is_emoji('d'))
        self.assertFalse(wfbot.is_emoji('!'))
        self.assertFalse(wfbot.is_emoji('¤'))
        self.assertFalse(wfbot.is_emoji('👨🛹2121'))
        self.assertFalse(wfbot.is_emoji('2121👨🛹'))
        self.assertFalse(wfbot.is_emoji('👨2121🛹'))
        self.assertFalse(wfbot.is_emoji('njdwe"%¤%&!/'))


if __name__ == '__main__':
    unittest.main()
