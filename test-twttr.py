import unittest
from twttr import shorten

class TestShorten(unittest.TestCase):
    def test_shorten_CS50(self):
        self.assertEqual(shorten("CS50"), "CS50")
    
    def test_shorten_AI(self):
        self.assertEqual(shorten("Artificial Intelligence"), "rtfcl ntllgnc")
    
    def test_shorten_Twitter(self):
        self.assertEqual(shorten("Twitter"), "Twttr")
    
    def test_shorten_name(self):
        self.assertEqual(shorten("What's your name?"), "Wht's yr nm?")

if __name__ == '__main__':
    unittest.main()
