from abc import ABC, abstractmethod
from typing import Optional, List
from yasinfeed.models import FeedSource, Article, User, Session

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
    def save_user(self, user: User) -> None:
        """Saves or updates a User in the store."""
        pass

    @abstractmethod
    def get_user(self, user_id: str) -> Optional[User]:
        """Retrieves a User by their unique ID."""
        pass

    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieves a User by their unique username."""
        pass

    @abstractmethod
    def list_users(self) -> List[User]:
        """Lists all stored User entities."""
        pass

    @abstractmethod
    def save_session(self, session: Session) -> None:
        """Saves or updates a Session in the store."""
        pass

    @abstractmethod
    def get_session(self, token: str) -> Optional[Session]:
        """Retrieves a Session by its unique token."""
        pass

    @abstractmethod
    def delete_session(self, token: str) -> None:
        """Deletes/invalidates a Session by its token."""
        pass

    @abstractmethod
    def list_sessions(self) -> List[Session]:
        """Lists all stored Session entities."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Closes any open database/file connections gracefully."""
        pass
