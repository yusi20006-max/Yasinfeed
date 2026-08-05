import unittest
from yasinfeed.normalize import normalize

class T(unittest.TestCase):
    def test_norm(self):
        self.assertEqual(normalize(" a   b "), "a b")

if __name__=="__main__":
    unittest.main()
