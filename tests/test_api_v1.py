import unittest
from yasinfeed.api.v1 import APIv1

class T(unittest.TestCase):
    def test_health(self):
        self.assertEqual(APIv1().health()["status"],"ok")

if __name__=="__main__":
    unittest.main()
