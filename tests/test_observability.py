import json
import os
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone

from yasinfeed.engine import YasinFeedEngine
from yasinfeed.monitoring import Metrics, MonitoringModule
from yasinfeed.monitoring.logging import StructuredEventLogger


class TestObservabilitySystem(unittest.TestCase):

    def test_thread_safe_metrics_concurrent_increment(self) -> None:
        """Test that Metrics operations are thread-safe under concurrent stress."""
        metrics = Metrics()
        metrics.set("api_calls", 0)

        # Number of threads and iterations per thread
        num_threads = 10
        iterations = 100

        def worker():
            for _ in range(iterations):
                metrics.inc("api_calls")

        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Expected value is num_threads * iterations
        self.assertEqual(metrics.get("api_calls"), num_threads * iterations)

    def test_timing_context_manager_and_decorator(self) -> None:
        """Test execution timing tracking with context manager and decorator."""
        metrics = Metrics()

        # 1. Test Context Manager
        with metrics.timing("db_fetch"):
            time.sleep(0.05)

        self.assertEqual(metrics.get("db_fetch_executions_total"), 1)
        self.assertGreater(metrics.get("db_fetch_last_duration_seconds"), 0.04)
        self.assertGreater(metrics.get("db_fetch_duration_seconds_total"), 0.04)
        self.assertGreater(metrics.get("db_fetch_average_duration_seconds"), 0.04)

        # Execute again to test count and averages
        with metrics.timing("db_fetch"):
            time.sleep(0.02)

        self.assertEqual(metrics.get("db_fetch_executions_total"), 2)
        self.assertGreater(metrics.get("db_fetch_duration_seconds_total"), 0.06)

        # 2. Test Decorator
        @metrics.time_func("my_custom_task")
        def dummy_function():
            time.sleep(0.01)
            return "ok"

        res = dummy_function()
        self.assertEqual(res, "ok")
        self.assertEqual(metrics.get("my_custom_task_executions_total"), 1)
        self.assertGreater(metrics.get("my_custom_task_last_duration_seconds"), 0.0)

    def test_detailed_error_metrics(self) -> None:
        """Test recording of error counts, types, and error metadata snapshots."""
        metrics = Metrics()
        metrics.record_error("fetch", "ConnectionTimeout", "Timeout connecting to remote RSS feed")

        self.assertEqual(metrics.get("total_errors"), 1)
        self.assertEqual(metrics.get("errors_fetch_total"), 1)

        errors_map = metrics.get_errors()
        self.assertIn("fetch", errors_map)
        self.assertEqual(errors_map["fetch"]["type"], "ConnectionTimeout")
        self.assertEqual(errors_map["fetch"]["message"], "Timeout connecting to remote RSS feed")
        self.assertIsNotNone(errors_map["fetch"]["timestamp"])

        # Run .all() snapshot and assert
        snapshot = metrics.all()
        self.assertEqual(snapshot["total_errors"], 1)
        self.assertEqual(snapshot["errors_fetch_total"], 1)
        self.assertIn("_error_details", snapshot)
        self.assertEqual(snapshot["_error_details"]["fetch"]["type"], "ConnectionTimeout")

    def test_structured_event_logging(self) -> None:
        """Test structured event logger formats JSON payload correctly and handles fallback."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            logger = StructuredEventLogger(log_path=tmp_path)
            logger.log_event(
                event_type="article_processed",
                severity="info",
                module="rewrite",
                message="Successfully summarized article ID 123",
                details={"duration_seconds": 0.45, "engine": "ollama"}
            )

            # Read log file and parse JSON lines
            with open(tmp_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            self.assertEqual(len(lines), 1)
            event = json.loads(lines[0])

            self.assertEqual(event["event_type"], "article_processed")
            self.assertEqual(event["severity"], "INFO")
            self.assertEqual(event["module"], "rewrite")
            self.assertEqual(event["message"], "Successfully summarized article ID 123")
            self.assertEqual(event["details"]["duration_seconds"], 0.45)
            self.assertIsNotNone(event["timestamp"])

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_api_health_payload_observability(self) -> None:
        """Test that MonitoringModule.get_system_status returns detailed observability telemetry."""
        engine = YasinFeedEngine(config_path="/path/to/nonexistent/config.yaml")
        engine.initialize()

        monitoring_mod = engine.modules["monitoring"]
        # Trigger some artificial metrics
        monitoring_mod.metrics.inc("api_requests", 4)
        monitoring_mod.metrics.record_error("storage", "SQLiteError", "Database table locked")

        status = monitoring_mod.get_system_status()
        self.assertIn(status["status"], ("healthy", "degraded", "unhealthy"))
        self.assertIn("metrics", status)
        self.assertIn("errors", status)
        self.assertEqual(status["metrics"]["api_requests"], 4)
        self.assertEqual(status["errors"]["total_errors"], 1)
        self.assertIn("storage", status["errors"]["last_errors"])


if __name__ == "__main__":
    unittest.main()
