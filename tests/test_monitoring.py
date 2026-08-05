import unittest
from yasinfeed.monitoring import Metrics

class T(unittest.TestCase):
    def test_metrics(self):
        m=Metrics()
        m.set("jobs",3)
        self.assertEqual(m.all()["jobs"],3)

if __name__=="__main__":
    unittest.main()
