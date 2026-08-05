import os
import unittest
import shutil
from datetime import datetime, timezone
from yasinfeed.engine import YasinFeedEngine
from yasinfeed.models import FeedSource, Article
from yasinfeed.storage import StorageModule
from yasinfeed.storage.sqlite import SQLiteStorage
from yasinfeed.storage.json_storage import JSONStorage

class TestStorage(unittest.TestCase):
    def setUp(self):
        # Create a temp directory for test database and files
        self.test_dir = "tests/temp_storage_test"
        os.makedirs(self.test_dir, exist_ok=True)
        self.sqlite_path = os.path.join(self.test_dir, "test_db.db")
        self.json_path = os.path.join(self.test_dir, "test_store.json")

    def tearDown(self):
        # Clean up temp directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_sqlite_storage_initialization(self):
        """Test SQLite backend creates tables upon initialization."""
        storage = SQLiteStorage(self.sqlite_path)
        self.assertTrue(os.path.exists(self.sqlite_path))
        storage.close()

    def test_sqlite_save_and_load_feed_source(self):
        """Test save, get, and list operation for FeedSource with SQLite backend."""
        storage = SQLiteStorage(self.sqlite_path)

        feed_source = FeedSource(
            id="source-1",
            url="https://example.com/feed.xml",
            name="Example Feed",
            enabled=True,
            last_fetched_at=datetime(2026, 8, 5, 12, 0, 0, tzinfo=timezone.utc)
        )

        # Save operation
        storage.save_feed_source(feed_source)

        # Load operation (get)
        retrieved = storage.get_feed_source("source-1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "source-1")
        self.assertEqual(retrieved.url, "https://example.com/feed.xml")
        self.assertEqual(retrieved.name, "Example Feed")
        self.assertTrue(retrieved.enabled)
        self.assertEqual(retrieved.last_fetched_at.year, 2026)

        # Update operation
        feed_source.name = "Updated Example Feed"
        feed_source.enabled = False
        storage.save_feed_source(feed_source)

        retrieved_updated = storage.get_feed_source("source-1")
        self.assertEqual(retrieved_updated.name, "Updated Example Feed")
        self.assertFalse(retrieved_updated.enabled)

        # List operation
        all_sources = storage.list_feed_sources()
        self.assertEqual(len(all_sources), 1)
        self.assertEqual(all_sources[0].id, "source-1")

        storage.close()

    def test_sqlite_save_and_load_article(self):
        """Test save, get, and list operation for Article with SQLite backend."""
        storage = SQLiteStorage(self.sqlite_path)

        article = Article(
            id="article-1",
            source_id="source-1",
            title="Breaking News",
            content="This is the article content.",
            original_url="https://example.com/article-1",
            published_at=datetime(2026, 8, 5, 12, 10, 0, tzinfo=timezone.utc),
            rewritten_content=None,
            rewrite_status="pending",
            published_outputs=["eitaa"]
        )

        # Save operation
        storage.save_article(article)

        # Load operation
        retrieved = storage.get_article("article-1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "article-1")
        self.assertEqual(retrieved.title, "Breaking News")
        self.assertEqual(retrieved.content, "This is the article content.")
        self.assertEqual(retrieved.rewrite_status, "pending")
        self.assertEqual(retrieved.published_outputs, ["eitaa"])

        # Update operation
        article.rewritten_content = "Rewritten content here."
        article.rewrite_status = "completed"
        article.published_outputs = ["eitaa", "rss"]
        storage.save_article(article)

        retrieved_updated = storage.get_article("article-1")
        self.assertEqual(retrieved_updated.rewritten_content, "Rewritten content here.")
        self.assertEqual(retrieved_updated.rewrite_status, "completed")
        self.assertEqual(retrieved_updated.published_outputs, ["eitaa", "rss"])

        # List operation
        all_articles = storage.list_articles()
        self.assertEqual(len(all_articles), 1)
        self.assertEqual(all_articles[0].id, "article-1")

        storage.close()

    def test_json_storage_initialization(self):
        """Test JSON backend initializes properly."""
        storage = JSONStorage(self.json_path)
        # Should create the empty structure and write it on closing or saving
        storage.close()
        self.assertTrue(os.path.exists(self.json_path))

    def test_json_save_and_load_feed_source(self):
        """Test save, get, and list operation for FeedSource with JSON backend."""
        storage = JSONStorage(self.json_path)

        feed_source = FeedSource(
            id="source-2",
            url="https://example.com/feed2.xml",
            name="JSON Feed",
            enabled=True,
            last_fetched_at=datetime(2026, 8, 5, 12, 0, 0, tzinfo=timezone.utc)
        )

        # Save operation
        storage.save_feed_source(feed_source)

        # Load operation (get)
        retrieved = storage.get_feed_source("source-2")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "source-2")
        self.assertEqual(retrieved.url, "https://example.com/feed2.xml")
        self.assertTrue(retrieved.enabled)

        # Update operation
        feed_source.name = "Updated JSON Feed"
        storage.save_feed_source(feed_source)

        retrieved_updated = storage.get_feed_source("source-2")
        self.assertEqual(retrieved_updated.name, "Updated JSON Feed")

        # List operation
        all_sources = storage.list_feed_sources()
        self.assertEqual(len(all_sources), 1)
        self.assertEqual(all_sources[0].id, "source-2")

        storage.close()

    def test_json_save_and_load_article(self):
        """Test save, get, and list operation for Article with JSON backend."""
        storage = JSONStorage(self.json_path)

        article = Article(
            id="article-2",
            source_id="source-2",
            title="JSON News",
            content="This is the JSON article content.",
            original_url="https://example.com/article-2",
            published_at=datetime(2026, 8, 5, 12, 10, 0, tzinfo=timezone.utc),
            rewritten_content=None,
            rewrite_status="pending",
            published_outputs=["rss"]
        )

        # Save operation
        storage.save_article(article)

        # Load operation
        retrieved = storage.get_article("article-2")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "article-2")
        self.assertEqual(retrieved.title, "JSON News")
        self.assertEqual(retrieved.published_outputs, ["rss"])

        # Update operation
        article.rewritten_content = "JSON rewrites."
        article.rewrite_status = "completed"
        storage.save_article(article)

        retrieved_updated = storage.get_article("article-2")
        self.assertEqual(retrieved_updated.rewritten_content, "JSON rewrites.")
        self.assertEqual(retrieved_updated.rewrite_status, "completed")

        # List operation
        all_articles = storage.list_articles()
        self.assertEqual(len(all_articles), 1)
        self.assertEqual(all_articles[0].id, "article-2")

        storage.close()

    def test_storage_module_integration(self):
        """Test StorageModule integration with config loading sqlite backend."""
        engine = YasinFeedEngine()
        # Custom config overrides for test database
        engine.config = {
            "storage": {
                "type": "sqlite",
                "path": self.sqlite_path
            }
        }

        storage_module = StorageModule(engine)
        self.assertTrue(storage_module.initialize())
        self.assertTrue(storage_module.start())

        # Test FeedSource pass-through methods
        fs = FeedSource(id="mod-fs", url="url", name="name")
        storage_module.save_feed_source(fs)
        self.assertEqual(storage_module.get_feed_source("mod-fs").id, "mod-fs")
        self.assertEqual(len(storage_module.list_feed_sources()), 1)

        # Test Article pass-through methods
        art = Article(
            id="mod-art", source_id="mod-fs", title="T", content="C",
            original_url="U", published_at=datetime.now()
        )
        storage_module.save_article(art)
        self.assertEqual(storage_module.get_article("mod-art").id, "mod-art")
        self.assertEqual(len(storage_module.list_articles()), 1)

        self.assertTrue(storage_module.stop())
