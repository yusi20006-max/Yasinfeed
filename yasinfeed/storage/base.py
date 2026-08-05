from abc import ABC, abstractmethod
from typing import Optional, List
from yasinfeed.models import FeedSource, Article

class StorageBackend(ABC):
    """
    Abstract Base Class for all storage backends in YasinFeed.
    """

    @abstractmethod
    def save_feed_source(self, feed_source: FeedSource) -> None:
        """Saves or updates a FeedSource in the store."""
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
        """Saves or updates an Article in the store."""
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
        """Closes any open database/file connections gracefully."""
        pass
