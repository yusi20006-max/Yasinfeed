import unittest
from yasinfeed.publish.pipeline import PublishPipeline

class Target:
    def __init__(self):
        self.ok=False
    def publish(self,a):
        self.ok=True

class T(unittest.TestCase):
    def test_publish(self):
        t=Target()
        p=PublishPipeline()
        p.register(t)
        p.publish({})
        self.assertTrue(t.ok)

if __name__=="__main__":
    unittest.main()
