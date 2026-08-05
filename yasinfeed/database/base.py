from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from yasinfeed.models import FeedSource, Article


class DatabaseError(Exception):
    """Base exception for all database provider operations."""
    pass


class DatabaseConfigurationError(DatabaseError):
    """Raised when there is a configuration issue with a database provider."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when connecting to a database fails."""
    pass


class BaseDatabaseProvider(ABC):
    """
    Abstract Base Class for all database providers in YasinFeed.
    All future database providers (SQLite, PostgreSQL, MySQL) must implement this interface.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        self.validate_config()
        self.connect()

    @abstractmethod
    def validate_config(self) -> None:
        """
        Validates the configuration keys and values.
        Raises DatabaseConfigurationError if invalid.
        """
        pass

    @abstractmethod
    def connect(self) -> None:
        """
        Establishes connection to the database.
        Raises DatabaseConnectionError if the connection fails.
        """
        pass

    @abstractmethod
    def save_feed_source(self, feed_source: FeedSource) -> None:
        """Saves or updates a FeedSource in the database."""
        pass

    @abstractmethod
    def get_feed_source(self, feed_source_id: str) -> Optional[FeedSource]:
        """Retrieves a FeedSource by its unique ID."""
        pass

    @abstractmethod
    def list_feed_sources(self) -> List[FeedSource]:
        """Lists all stored FeedSource entities."""
        pass

    @abstractmethod
    def save_article(self, article: Article) -> None:
        """Saves or updates an Article in the database."""
        pass

    @abstractmethod
    def get_article(self, article_id: str) -> Optional[Article]:
        """Retrieves an Article by its unique ID."""
        pass

    @abstractmethod
    def list_articles(self) -> List[Article]:
        """Lists all stored Article entities."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Closes the database connection gracefully."""
        pass
