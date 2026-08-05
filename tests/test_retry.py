import unittest
from yasinfeed.retry import retry

class T(unittest.TestCase):
    def test_retry(self):
        c={"n":0}
        def f():
            c["n"]+=1
            if c["n"]<3:
                raise Exception()
            return "ok"
        self.assertEqual(retry(f),"ok")

if __name__=="__main__":
    unittest.main()
