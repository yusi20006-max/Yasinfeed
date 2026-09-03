import sys
import unittest
import os
import platform
from datetime import datetime, timezone

from yasinfeed.engine import YasinFeedEngine
from yasinfeed.models import Article, FeedSource
from yasinfeed.fetch.parser import FeedItem, RSSParser
from yasinfeed.rewrite.providers.factory import create_provider
from yasinfeed.rewrite.providers.base import BaseAIProvider, AIConfigurationError

class TestTermuxPython314Compat(unittest.TestCase):

    def test_python_runtime_version_support(self):
        """Verify running Python version meets minimum >= 3.8 contract."""
        self.assertGreaterEqual(sys.version_info[:2], (3, 8))

    def test_std_lib_modules_availability(self):
        """Verify pure-Python stdlib modules required for Android/Termux environments."""
        import sqlite3
        import urllib.request
        import threading
        import xml.etree.ElementTree
        import hashlib
        import secrets

        self.assertIsNotNone(sqlite3)
        self.assertIsNotNone(urllib)
        self.assertIsNotNone(threading)

    def test_timezone_aware_datetime_handling(self):
        """Verify datetime ISO parsing/formatting without deprecated utcnow in Python 3.14."""
        now_utc = datetime.now(timezone.utc)
        self.assertIsNotNone(now_utc.tzinfo)
        iso_str = now_utc.isoformat()
        parsed = datetime.fromisoformat(iso_str)
        self.assertEqual(now_utc, parsed)

    def test_rss_parser_datetime_compat(self):
        """Verify FeedItem initializes with timezone-aware datetime."""
        item = FeedItem(title="Test", link="https://example.com", content="Test content")
        self.assertIsNotNone(item.published_at.tzinfo)

    def test_yasinai_optional_provider_contract(self):
        """Verify Yasin-AI remains an optional provider raising AIConfigurationError when not installed."""
        try:
            import yasinai
            yasinai_installed = True
        except ImportError:
            yasinai_installed = False

        if not yasinai_installed:
            with self.assertRaises(AIConfigurationError):
                create_provider("yasinai", {})
        else:
            provider = create_provider("yasinai", {})
            self.assertIsInstance(provider, BaseAIProvider)

    def test_main_engine_instantiation(self):
        """Verify core YasinFeedEngine initializes cleanly without external system dependencies."""
        engine = YasinFeedEngine()
        success = engine.initialize()
        self.assertTrue(success)

if __name__ == "__main__":
    unittest.main()
