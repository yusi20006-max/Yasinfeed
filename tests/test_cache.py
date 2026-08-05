import unittest
from yasinfeed.cache.cache import Cache

class T(unittest.TestCase):
    def test_cache(self):
        c=Cache()
        c.set("a",1)
        self.assertEqual(c.get("a"),1)

if __name__=="__main__":
    unittest.main()
