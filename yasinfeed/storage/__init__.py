from typing import Optional, List
from yasinfeed.engine import BaseModule
from yasinfeed.models import FeedSource, Article
from yasinfeed.storage.base import StorageBackend
from yasinfeed.storage.sqlite import SQLiteStorage
from yasinfeed.storage.json_storage import JSONStorage

class StorageModule(BaseModule):
    """
    Handles local data storage, database connections, and migrations.
    Supported types: sqlite, json.
    Exposes high-level storage save, load, and listing operations.
    """
    def initialize(self) -> bool:
        self.logger.info("Initializing storage module...")
        self.storage_type = self.config.get("storage", {}).get("type", "sqlite")
        self.storage_path = self.config.get("storage", {}).get("path", "data/yasinfeed.db")
        self.logger.info("Storage backend: %s at %s", self.storage_type, self.storage_path)

        # Initialize the appropriate backend based on configuration
        try:
            if self.storage_type == "json":
                self.backend: StorageBackend = JSONStorage(self.storage_path)
            else:
                self.backend = SQLiteStorage(self.storage_path)
        except Exception as e:
            self.logger.error("Failed to initialize storage backend: %s", e, exc_info=True)
            return False

        return True

    def start(self) -> bool:
        self.logger.info("Storage module started. Connection pool established.")
        return True

    def stop(self) -> bool:
        try:
            if hasattr(self, 'backend') and self.backend:
                self.backend.close()
        except Exception as e:
            self.logger.warning("Error during closing storage backend: %s", e)
        self.logger.info("Storage module stopped. Connection pool released.")
        return True

    def save_feed_source(self, feed_source: FeedSource) -> None:
        """Saves or updates a FeedSource using the active storage backend."""
        self.backend.save_feed_source(feed_source)

    def get_feed_source(self, feed_source_id: str) -> Optional[FeedSource]:
        """Retrieves a FeedSource by its unique ID."""
        return self.backend.get_feed_source(feed_source_id)

    def list_feed_sources(self) -> List[FeedSource]:
        """Lists all stored FeedSources."""
        return self.backend.list_feed_sources()

    def save_article(self, article: Article) -> None:
        """Saves or updates an Article using the active storage backend."""
        self.backend.save_article(article)

    def get_article(self, article_id: str) -> Optional[Article]:
        """Retrieves an Article by its unique ID."""
        return self.backend.get_article(article_id)

    def list_articles(self) -> List[Article]:
        """Lists all stored Articles."""
        return self.backend.list_articles()
