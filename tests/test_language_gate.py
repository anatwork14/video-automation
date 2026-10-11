import unittest
from validate import contains_vietnamese_prose

class LanguageGateTests(unittest.TestCase):
    def test_vietnamese_storyboard_is_detected(self):
        self.assertTrue(contains_vietnamese_prose("Dung nham chảy ra biển"))
        self.assertTrue(contains_vietnamese_prose("SỤT LÚN"))
    def test_english_prose_is_not_blocked(self):
        self.assertFalse(contains_vietnamese_prose("REAL FOOTAGE | SUMMIT COLLAPSE"))
        self.assertFalse(contains_vietnamese_prose("Kīlauea Hawaii"))
