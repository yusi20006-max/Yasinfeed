import unittest
from yasinfeed.ai.failover import FailoverProvider

class Bad:
    def rewrite(self,t):
        raise Exception()

class Good:
    def rewrite(self,t):
        return "OK"

class T(unittest.TestCase):
    def test_fail(self):
        f=FailoverProvider(Bad(),Good())
        self.assertEqual(f.rewrite("x"),"OK")

if __name__=="__main__":
    unittest.main()
