from typing import Optional, List
from yasinfeed.engine import BaseModule
from yasinfeed.models import FeedSource, Article, User, Session
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

    def _get_monitoring(self):
        if hasattr(self, 'engine') and self.engine:
            return self.engine.modules.get("monitoring")
        return None

    def save_feed_source(self, feed_source: FeedSource) -> None:
        """Saves or updates a FeedSource using the active storage backend."""
        monitoring = self._get_monitoring()
        if monitoring:
            monitoring.metrics.inc("db_queries")
            with monitoring.metrics.timing("db_save_feed_source"):
                self.backend.save_feed_source(feed_source)
        else:
            self.backend.save_feed_source(feed_source)

    def get_feed_source(self, feed_source_id: str) -> Optional[FeedSource]:
        """Retrieves a FeedSource by its unique ID."""
        monitoring = self._get_monitoring()
        if monitoring:
            monitoring.metrics.inc("db_queries")
            with monitoring.metrics.timing("db_get_feed_source"):
                return self.backend.get_feed_source(feed_source_id)
        else:
            return self.backend.get_feed_source(feed_source_id)

    def list_feed_sources(self) -> List[FeedSource]:
        """Lists all stored FeedSources."""
        monitoring = self._get_monitoring()
        if monitoring:
            monitoring.metrics.inc("db_queries")
            with monitoring.metrics.timing("db_list_feed_sources"):
                return self.backend.list_feed_sources()
        else:
            return self.backend.list_feed_sources()

    def save_article(self, article: Article) -> None:
        """Saves or updates an Article using the active storage backend."""
        monitoring = self._get_monitoring()
        if monitoring:
            monitoring.metrics.inc("db_queries")
            with monitoring.metrics.timing("db_save_article"):
                self.backend.save_article(article)
        else:
            self.backend.save_article(article)

    def get_article(self, article_id: str) -> Optional[Article]:
        """Retrieves an Article by its unique ID."""
        monitoring = self._get_monitoring()
        if monitoring:
            monitoring.metrics.inc("db_queries")
            with monitoring.metrics.timing("db_get_article"):
                return self.backend.get_article(article_id)
        else:
            return self.backend.get_article(article_id)

    def list_articles(self) -> List[Article]:
        """Lists all stored Articles."""
        monitoring = self._get_monitoring()
        if monitoring:
            monitoring.metrics.inc("db_queries")
            with monitoring.metrics.timing("db_list_articles"):
                return self.backend.list_articles()
        else:
            return self.backend.list_articles()

    def save_user(self, user: User) -> None:
        """Saves or updates a User using the active storage backend."""
        self.backend.save_user(user)

    def get_user(self, user_id: str) -> Optional[User]:
        """Retrieves a User by their unique ID."""
        return self.backend.get_user(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieves a User by their unique username."""
        return self.backend.get_user_by_username(username)

    def list_users(self) -> List[User]:
        """Lists all stored Users."""
        return self.backend.list_users()

    def save_session(self, session: Session) -> None:
        """Saves or updates a Session using the active storage backend."""
        self.backend.save_session(session)

    def get_session(self, token: str) -> Optional[Session]:
        """Retrieves a Session by its unique token."""
        return self.backend.get_session(token)

    def delete_session(self, token: str) -> None:
        """Deletes/invalidates a Session by its token."""
        self.backend.delete_session(token)

    def list_sessions(self) -> List[Session]:
        """Lists all stored Sessions."""
        return self.backend.list_sessions()
