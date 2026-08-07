import unittest
from unittest.mock import MagicMock, patch
import json
import time
import os
import shutil
import threading
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import HTTPError

from yasinfeed.engine import YasinFeedEngine
from yasinfeed.models import FeedSource, Article
from yasinfeed.fetch import FetchModule


class TestMultiSourceAggregation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = "tests/temp_multi_test"
        os.makedirs(cls.temp_dir, exist_ok=True)
        cls.config_path = os.path.join(cls.temp_dir, "config.yaml")

        # Write temporary YAML config
        config_content = """
storage:
  type: json
  path: tests/temp_multi_test/storage.json
api:
  host: 127.0.0.1
  port: 0
  security:
    enabled: true
    rate_limit_per_minute: 50
    admin_api_key: secret-admin-key
    token_expiry_hours: 1
fetch:
  interval_seconds: 100
  content_merge_strategy: priority
"""
        with open(cls.config_path, "w", encoding="utf-8") as f:
            f.write(config_content)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    def setUp(self):
        storage_path = "tests/temp_multi_test/storage.json"
        if os.path.exists(storage_path):
            try:
                os.remove(storage_path)
            except OSError:
                pass
        self.engine = YasinFeedEngine(self.config_path)
        self.engine.initialize()

    def tearDown(self):
        self.engine.stop()

    def test_feed_source_attributes_loading_saving(self):
        storage = self.engine.modules["storage"]
        src = FeedSource(
            id="src-1",
            name="Source 1",
            url="http://src1.feed",
            priority=10,
            weight=2.5,
            reliability_score=0.9
        )
        storage.save_feed_source(src)

        loaded = storage.get_feed_source("src-1")
        self.assertEqual(loaded.priority, 10)
        self.assertEqual(loaded.weight, 2.5)
        self.assertEqual(loaded.reliability_score, 0.9)

    @patch("yasinfeed.fetch.fetcher.FeedFetcher.fetch")
    def test_multi_source_aggregation_priority_merge(self, mock_fetch):
        storage = self.engine.modules["storage"]
        fetch_mod = self.engine.modules["fetch"]

        # Configure two sources with different priorities
        src_low = FeedSource(id="src-low", name="Low Priority Source", url="http://low.feed", priority=1)
        src_high = FeedSource(id="src-high", name="High Priority Source", url="http://high.feed", priority=10)
        storage.save_feed_source(src_low)
        storage.save_feed_source(src_high)

        # Mock entries representing identical articles (duplicate normalized title)
        feed_low = MagicMock()
        entry_low = MagicMock()
        entry_low.title = "Identical Title"
        entry_low.description = "Low priority content"
        entry_low.link = "http://identical.url"
        feed_low.entries = [entry_low]

        feed_high = MagicMock()
        entry_high = MagicMock()
        entry_high.title = "Identical Title  " # extra space to test normalization
        entry_high.description = "High priority content"
        entry_high.link = "http://identical.url"
        feed_high.entries = [entry_high]

        def mock_fetch_side_effect(url):
            if "low" in url:
                return feed_low
            return feed_high

        mock_fetch.side_effect = mock_fetch_side_effect

        # Fetch sources and perform priority merge
        fetch_mod.content_merge_strategy = "priority"
        results = fetch_mod.fetch_sources()

        self.assertEqual(len(results), 1)
        # Should have chosen high priority content
        self.assertEqual(results[0]["content"], "High priority content")
        self.assertEqual(results[0]["source_id"], "src-high")

    @patch("yasinfeed.fetch.fetcher.FeedFetcher.fetch")
    def test_multi_source_aggregation_combine_merge(self, mock_fetch):
        storage = self.engine.modules["storage"]
        fetch_mod = self.engine.modules["fetch"]

        src_low = FeedSource(id="src-low", name="Low Source", url="http://low.feed", priority=1)
        src_high = FeedSource(id="src-high", name="High Source", url="http://high.feed", priority=10)
        storage.save_feed_source(src_low)
        storage.save_feed_source(src_high)

        feed_low = MagicMock()
        entry_low = MagicMock()
        entry_low.title = "Identical Title"
        entry_low.description = "Low priority content"
        entry_low.link = "http://identical.url"
        feed_low.entries = [entry_low]

        feed_high = MagicMock()
        entry_high = MagicMock()
        entry_high.title = "Identical Title"
        entry_high.description = "High priority content"
        entry_high.link = "http://identical.url"
        feed_high.entries = [entry_high]

        mock_fetch.side_effect = lambda url: feed_low if "low" in url else feed_high

        # Fetch with 'combine' strategy
        fetch_mod.content_merge_strategy = "combine"
        results = fetch_mod.fetch_sources()

        self.assertEqual(len(results), 1)
        # Should have combined both contents
        combined_text = results[0]["content"]
        self.assertIn("High priority content", combined_text)
        self.assertIn("Low priority content", combined_text)
        self.assertIn("Alternative Content from Low Source", combined_text)

    @patch("yasinfeed.fetch.fetcher.FeedFetcher.fetch")
    def test_failure_isolation_and_reliability_tracking(self, mock_fetch):
        storage = self.engine.modules["storage"]
        fetch_mod = self.engine.modules["fetch"]

        src_fail = FeedSource(id="src-fail", name="Failing Source", url="http://fail.feed")
        src_ok = FeedSource(id="src-ok", name="Working Source", url="http://ok.feed")
        storage.save_feed_source(src_fail)
        storage.save_feed_source(src_ok)

        feed_ok = MagicMock()
        entry_ok = MagicMock()
        entry_ok.title = "Good News"
        entry_ok.description = "Working content"
        entry_ok.link = "http://good.url"
        feed_ok.entries = [entry_ok]

        def mock_fetch_side_effect(url):
            if "fail" in url:
                raise ValueError("Network Timeout")
            return feed_ok

        mock_fetch.side_effect = mock_fetch_side_effect

        results = fetch_mod.fetch_sources()

        # Success items from src-ok should still be returned (Failure Isolation)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Good News")

        # Check reliability stats updated in database
        loaded_fail = storage.get_feed_source("src-fail")
        self.assertEqual(loaded_fail.fetch_count, 1)
        self.assertEqual(loaded_fail.failure_count, 1)
        self.assertEqual(loaded_fail.reliability_score, 0.0)
        self.assertIn("Network Timeout", loaded_fail.last_error)

        loaded_ok = storage.get_feed_source("src-ok")
        self.assertEqual(loaded_ok.fetch_count, 1)
        self.assertEqual(loaded_ok.success_count, 1)
        self.assertEqual(loaded_ok.reliability_score, 1.0)

    def test_api_security_enforcement_and_api_key_validation(self):
        # Prevent port collision by dynamically allocating port
        api_mod = self.engine.modules["api"]
        api_mod.port = 0

        # Start API server
        self.engine_thread = threading.Thread(target=self.engine.start)
        self.engine_thread.daemon = True
        self.engine_thread.start()

        # Wait for port to be assigned
        start_time = time.time()
        while time.time() - start_time < 3.0:
            if hasattr(api_mod, "port") and api_mod.port != 0:
                break
            time.sleep(0.05)

        base_url = f"http://127.0.0.1:{api_mod.port}"

        # 1. Request GET /api/sources without authorization header -> should return 401 Unauthorized
        req_unauth = Request(f"{base_url}/api/sources")
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req_unauth)
        self.assertEqual(ctx.exception.code, 401)
        err_msg = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertEqual(err_msg["error"], "Unauthorized")

        # 2. Request GET /api/sources with invalid API key -> should return 401 Unauthorized
        req_bad_key = Request(f"{base_url}/api/sources", headers={"X-API-Key": "wrong-key"})
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req_bad_key)
        self.assertEqual(ctx.exception.code, 401)

        # 3. Request GET /api/sources with valid admin API key in X-API-Key -> should succeed
        req_good_key = Request(f"{base_url}/api/sources", headers={"X-API-Key": "secret-admin-key"})
        with urlopen(req_good_key) as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertIsInstance(data, list)

        # 4. Request GET /api/sources with valid Key Authorization header -> should succeed
        req_good_auth = Request(f"{base_url}/api/sources", headers={"Authorization": "Key secret-admin-key"})
        with urlopen(req_good_auth) as response:
            self.assertEqual(response.status, 200)

        # 5. Security headers presence
        with urlopen(req_good_key) as response:
            headers = dict(response.headers)
            self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
            self.assertEqual(headers.get("X-Frame-Options"), "DENY")
            self.assertIn("Content-Security-Policy", headers)


if __name__ == "__main__":
    unittest.main()
