import unittest

from yasinfeed.monitoring import Metrics
from yasinfeed.dashboard import Dashboard

class TestDashboard(unittest.TestCase):

    def test_summary(self):
        metrics = Metrics()
        metrics.set("feeds", 5)
        metrics.set("articles", 12)

        dashboard = Dashboard(metrics)
        data = dashboard.summary()

        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["metrics"]["feeds"], 5)
        self.assertEqual(data["metrics"]["articles"], 12)

if __name__ == "__main__":
    unittest.main()
