from typing import Optional, List
from yasinfeed.models import FeedSource, Article
from yasinfeed.storage.base import StorageBackend
from yasinfeed.database.factory import create_db_provider


class SQLiteStorage(StorageBackend):
    """
    SQLite-backed storage implementation for YasinFeed.
    Delegates database operations to the modular database layer.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        # Instantiate SQLite provider from the modular database layer
        self.provider = create_db_provider("sqlite", {"path": db_path})

    def save_feed_source(self, feed_source: FeedSource) -> None:
        """Saves or updates a FeedSource using the delegated provider."""
        self.provider.save_feed_source(feed_source)

    def get_feed_source(self, feed_source_id: str) -> Optional[FeedSource]:
        """Retrieves a FeedSource by its unique ID."""
        return self.provider.get_feed_source(feed_source_id)

    def list_feed_sources(self) -> List[FeedSource]:
        """Lists all stored FeedSource entities."""
        return self.provider.list_feed_sources()

    def save_article(self, article: Article) -> None:
        """Saves or updates an Article using the delegated provider."""
        self.provider.save_article(article)

    def get_article(self, article_id: str) -> Optional[Article]:
        """Retrieves an Article by its unique ID."""
        return self.provider.get_article(article_id)

    def list_articles(self) -> List[Article]:
        """Lists all stored Article entities."""
        return self.provider.list_articles()

    def close(self) -> None:
        """Closes any open database connections gracefully."""
        self.provider.close()
