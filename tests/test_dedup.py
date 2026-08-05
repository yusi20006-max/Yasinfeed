import unittest
from yasinfeed.dedup import Deduplicator

class T(unittest.TestCase):
    def test_dup(self):
        d=Deduplicator()
        self.assertTrue(d.add("abc"))
        self.assertFalse(d.add("abc"))

if __name__=="__main__":
    unittest.main()
