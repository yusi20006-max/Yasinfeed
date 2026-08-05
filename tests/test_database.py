import os
import shutil
import unittest
from datetime import datetime, timezone
from yasinfeed.models import FeedSource, Article
from yasinfeed.database import create_db_provider, BaseDatabaseProvider, DatabaseError, DatabaseConfigurationError, DatabaseConnectionError
from yasinfeed.database.sqlite import SQLiteDatabaseProvider


class TestDatabaseLayer(unittest.TestCase):
    def setUp(self):
        # Create a temp directory for testing database provider
        self.test_dir = "tests/temp_db_test"
        os.makedirs(self.test_dir, exist_ok=True)
        self.db_path = os.path.join(self.test_dir, "test_database.db")

    def tearDown(self):
        # Clean up database files and folder
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_factory_valid_creation(self):
        """Test that the factory successfully instantiates SQLiteDatabaseProvider."""
        provider = create_db_provider("sqlite", {"path": self.db_path})
        self.assertIsInstance(provider, SQLiteDatabaseProvider)
        self.assertIsInstance(provider, BaseDatabaseProvider)
        provider.close()

    def test_factory_invalid_provider_raises(self):
        """Test that passing an unsupported provider to the factory raises DatabaseConfigurationError."""
        with self.assertRaises(DatabaseConfigurationError):
            create_db_provider("postgres_unsupported", {"host": "localhost"})

    def test_sqlite_missing_config_raises(self):
        """Test that SQLite provider raises DatabaseConfigurationError when configuration is missing 'path'."""
        with self.assertRaises(DatabaseConfigurationError):
            create_db_provider("sqlite", {})
        with self.assertRaises(DatabaseConfigurationError):
            create_db_provider("sqlite", {"not_path": "invalid"})

    def test_sqlite_invalid_path_connection_error(self):
        """Test that SQLite provider raises DatabaseConnectionError when directory cannot be created."""
        # /sys/class/some_nonexistent_directory is generally read-only/unwritable on Linux
        with self.assertRaises(DatabaseConnectionError):
            create_db_provider("sqlite", {"path": "/sys/class/some_nonexistent_directory/test.db"})

    def test_sqlite_feed_source_crud(self):
        """Test CRUD operations for FeedSource utilizing SQLite database provider."""
        provider = create_db_provider("sqlite", {"path": self.db_path})

        fs = FeedSource(
            id="src-db-test",
            url="https://example.com/db.xml",
            name="DB Feed",
            enabled=True,
            last_fetched_at=datetime(2026, 8, 5, 22, 0, 0, tzinfo=timezone.utc)
        )

        # Create/Save
        provider.save_feed_source(fs)

        # Retrieve/Read
        retrieved = provider.get_feed_source("src-db-test")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "src-db-test")
        self.assertEqual(retrieved.url, "https://example.com/db.xml")
        self.assertEqual(retrieved.name, "DB Feed")
        self.assertTrue(retrieved.enabled)
        self.assertEqual(retrieved.last_fetched_at.year, 2026)

        # Update
        fs.name = "Updated DB Feed"
        fs.enabled = False
        provider.save_feed_source(fs)

        retrieved_updated = provider.get_feed_source("src-db-test")
        self.assertEqual(retrieved_updated.name, "Updated DB Feed")
        self.assertFalse(retrieved_updated.enabled)

        # List
        all_sources = provider.list_feed_sources()
        self.assertEqual(len(all_sources), 1)
        self.assertEqual(all_sources[0].id, "src-db-test")

        provider.close()

    def test_sqlite_article_crud(self):
        """Test CRUD operations for Article utilizing SQLite database provider."""
        provider = create_db_provider("sqlite", {"path": self.db_path})

        art = Article(
            id="art-db-test",
            source_id="src-db-test",
            title="Database Integration News",
            content="Highly modular database layer implemented for YasinFeed.",
            original_url="https://example.com/art-db-test",
            published_at=datetime(2026, 8, 5, 22, 15, 0, tzinfo=timezone.utc),
            rewritten_content=None,
            rewrite_status="pending",
            published_outputs=["eitaa", "rss"]
        )

        # Create/Save
        provider.save_article(art)

        # Retrieve/Read
        retrieved = provider.get_article("art-db-test")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "art-db-test")
        self.assertEqual(retrieved.title, "Database Integration News")
        self.assertEqual(retrieved.rewrite_status, "pending")
        self.assertEqual(retrieved.published_outputs, ["eitaa", "rss"])

        # Update
        art.rewritten_content = "Summary of DB implementation."
        art.rewrite_status = "completed"
        art.published_outputs = ["eitaa", "rss", "pwa"]
        provider.save_article(art)

        retrieved_updated = provider.get_article("art-db-test")
        self.assertEqual(retrieved_updated.rewritten_content, "Summary of DB implementation.")
        self.assertEqual(retrieved_updated.rewrite_status, "completed")
        self.assertEqual(retrieved_updated.published_outputs, ["eitaa", "rss", "pwa"])

        # List
        all_articles = provider.list_articles()
        self.assertEqual(len(all_articles), 1)
        self.assertEqual(all_articles[0].id, "art-db-test")

        provider.close()


if __name__ == "__main__":
    unittest.main()
