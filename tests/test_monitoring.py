import os
import unittest
from yasinfeed.engine import YasinFeedEngine
from yasinfeed.monitoring import Metrics, MonitoringModule


class TestMonitoringSystem(unittest.TestCase):

    def test_metrics_foundation(self):
        """Test the metrics class and standard metric operations."""
        m = Metrics()
        # Test basic set/get
        m.set("api_calls", 10)
        self.assertEqual(m.get("api_calls"), 10)

        # Test increment
        m.inc("articles_fetched", 5)
        self.assertEqual(m.get("articles_fetched"), 5)
        m.inc("articles_fetched")
        self.assertEqual(m.get("articles_fetched"), 6)

        # Test all metrics dictionary retrieval
        all_metrics = m.all()
        self.assertEqual(all_metrics["api_calls"], 10)
        self.assertEqual(all_metrics["articles_fetched"], 6)

    def test_monitoring_module_lifecycle(self):
        """Test the initialization, startup, and teardown of the MonitoringModule."""
        # Use custom engine setup with nonexistent configuration path (loads defaults)
        engine = YasinFeedEngine(config_path="/path/to/nonexistent/config.yaml")
        success = engine.initialize()
        self.assertTrue(success)

        # Ensure MonitoringModule is registered and initialized
        self.assertIn("monitoring", engine.modules)
        monitoring_mod = engine.modules["monitoring"]
        self.assertTrue(isinstance(monitoring_mod, MonitoringModule))

        # Test metrics are initialized with default values
        self.assertEqual(monitoring_mod.metrics.get("api_requests"), 0)
        self.assertEqual(monitoring_mod.metrics.get("articles_processed"), 0)
        self.assertIsNotNone(monitoring_mod.metrics.get("startup_time"))

        # Test start and stop
        self.assertTrue(monitoring_mod.start())
        self.assertTrue(monitoring_mod.stop())

    def test_health_check_system(self):
        """Test health checks and system status reporting."""
        engine = YasinFeedEngine(config_path="/path/to/nonexistent/config.yaml")
        engine.initialize()

        monitoring_mod = engine.modules["monitoring"]

        # Run health check
        health = monitoring_mod.perform_health_check()
        self.assertIn("status", health)
        self.assertIn("checks", health)
        self.assertIn("timestamp", health)

        # Run full system status check
        status = monitoring_mod.get_system_status()
        self.assertIn("status", status)
        self.assertIn("system", status)
        self.assertIn("metrics", status)
        self.assertIn("checks", status)

        # Verify platform/OS details exist in system status
        self.assertIn("python_version", status["system"])
        self.assertIn("pid", status["system"])
        self.assertGreaterEqual(status["system"]["uptime_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
