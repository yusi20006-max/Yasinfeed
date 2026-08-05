import unittest
from yasinfeed.ai.router import AIRouter

class P:
    def rewrite(self,t):
        return t.upper()

class T(unittest.TestCase):
    def test_router(self):
        r=AIRouter()
        r.register(P())
        self.assertEqual(r.rewrite("abc"),"ABC")

if __name__=="__main__":
    unittest.main()
