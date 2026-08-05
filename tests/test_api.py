import json
import os
import shutil
import threading
import time
import unittest
from datetime import datetime, timezone
from urllib.request import urlopen
from urllib.error import HTTPError

from yasinfeed.engine import YasinFeedEngine
from yasinfeed.models import Article, FeedSource


class TestApiModule(unittest.TestCase):
    def setUp(self):
        # Setup clean temporary directory for sqlite storage
        self.test_dir = "tests/temp_api_test"
        os.makedirs(self.test_dir, exist_ok=True)
        self.db_path = os.path.join(self.test_dir, "test_api_db.db")

        # Custom config dict for engine initialization
        self.engine = YasinFeedEngine(config_path="/path/to/nonexistent/config.yaml")

        # Initialize engine first to load defaults
        self.engine.initialize()

        # Override configurations directly on the modules/engine to guarantee test isolation
        self.api_mod = self.engine.modules["api"]
        self.api_mod.port = 0  # Automatically bind to an available port
        self.api_mod.host = "127.0.0.1"

        self.storage_mod = self.engine.modules["storage"]
        self.storage_mod.storage_type = "sqlite"
        self.storage_mod.storage_path = self.db_path
        # Re-initialize storage backend with test path
        from yasinfeed.storage.sqlite import SQLiteStorage
        self.storage_mod.backend = SQLiteStorage(self.db_path)

        self.scheduler_mod = self.engine.modules["scheduler"]
        # Keep scheduler disabled to prevent background automation triggers
        self.scheduler_mod.enabled = False

        # Start the engine inside a background thread so we can stop it cleanly
        self.engine_thread = threading.Thread(target=self.engine.start)
        self.engine_thread.daemon = True
        self.engine_thread.start()

        # Wait up to 3 seconds for the API port to be assigned dynamically
        start_time = time.time()
        while time.time() - start_time < 3.0:
            if hasattr(self.api_mod, "port") and self.api_mod.port != 0:
                break
            time.sleep(0.05)

        # Base URL for requests
        self.base_url = f"http://127.0.0.1:{self.api_mod.port}"

    def tearDown(self):
        # Stop engine and clean up directory
        self.engine.stop()
        if hasattr(self, "engine_thread"):
            self.engine_thread.join(timeout=3.0)

        # Clean up logging handlers to avoid ResourceWarnings and clean up state
        import logging
        root_logger = logging.getLogger()
        for h in list(root_logger.handlers):
            h.close()
            root_logger.removeHandler(h)

        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except Exception:
                pass

    def test_health_endpoint(self):
        # Request health endpoint
        with urlopen(f"{self.base_url}/health") as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertEqual(data["status"], "ok")
            self.assertEqual(data["service"], "YasinFeed API Layer")
            self.assertIn("timestamp", data)

        # Request /api/health endpoint
        with urlopen(f"{self.base_url}/api/health") as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertEqual(data["status"], "ok")

    def test_articles_endpoint_empty(self):
        # Request articles list when empty
        with urlopen(f"{self.base_url}/api/articles") as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertEqual(data, [])

    def test_articles_endpoint_nonempty_and_get_by_id(self):
        # Insert raw article in storage
        art = Article(
            id="art123",
            source_id="src_tech",
            title="Python is amazing",
            content="Python is widely used in AI, web development, and backend services.",
            original_url="https://python.org",
            published_at=datetime.now(timezone.utc),
            rewritten_content="Python is great for backend development and artificial intelligence.",
            rewrite_status="completed",
            published_outputs=["eitaa", "rss"]
        )
        self.storage_mod.save_article(art)

        # Test GET list
        with urlopen(f"{self.base_url}/api/articles") as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["id"], "art123")
            self.assertEqual(data[0]["title"], "Python is amazing")
            self.assertEqual(data[0]["rewrite_status"], "completed")
            self.assertEqual(data[0]["published_outputs"], ["eitaa", "rss"])

        # Test GET single by query param
        with urlopen(f"{self.base_url}/api/articles?id=art123") as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertEqual(data["id"], "art123")
            self.assertEqual(data["title"], "Python is amazing")

        # Test GET single by path suffix
        with urlopen(f"{self.base_url}/api/articles/art123") as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertEqual(data["id"], "art123")

        # Test GET single nonexistent (query param)
        with self.assertRaises(HTTPError) as ctx:
            urlopen(f"{self.base_url}/api/articles?id=nonexistent")
        self.assertEqual(ctx.exception.code, 404)
        err_data = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertIn("error", err_data)

        # Test GET single nonexistent (path suffix)
        with self.assertRaises(HTTPError) as ctx:
            urlopen(f"{self.base_url}/api/articles/nonexistent")
        self.assertEqual(ctx.exception.code, 404)
        err_data = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertIn("error", err_data)

    def test_sources_endpoint(self):
        # Insert mock feed source
        source = FeedSource(
            id="src_ai",
            url="https://openai.com/feed.xml",
            name="OpenAI Blog",
            enabled=True,
            last_fetched_at=datetime.now(timezone.utc)
        )
        self.storage_mod.save_feed_source(source)

        # Retrieve via API
        with urlopen(f"{self.base_url}/api/sources") as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["id"], "src_ai")
            self.assertEqual(data[0]["name"], "OpenAI Blog")
            self.assertEqual(data[0]["enabled"], True)
            self.assertIsNotNone(data[0]["last_fetched_at"])

    def test_scheduler_endpoint(self):
        # Register a mock job on the scheduler
        self.scheduler_mod.scheduler.add_job(
            name="test_periodic_sync",
            func=lambda: None,
            interval=3600.0
        )

        with urlopen(f"{self.base_url}/api/scheduler") as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertEqual(data["enabled"], False)
            self.assertIn("jobs", data)
            self.assertIsInstance(data["jobs"], list)
            # Should contain our manually registered job
            self.assertTrue(any(j["name"] == "test_periodic_sync" for j in data["jobs"]))

    def test_error_handling(self):
        with self.assertRaises(HTTPError) as ctx:
            urlopen(f"{self.base_url}/api/nonexistent_route")
        self.assertEqual(ctx.exception.code, 404)
        data = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()
