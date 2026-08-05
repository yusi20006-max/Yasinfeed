import os
import json
import tempfile
from datetime import datetime
from typing import Optional, List, Dict, Any
from yasinfeed.models import FeedSource, Article
from yasinfeed.storage.base import StorageBackend

class JSONStorage(StorageBackend):
    """
    JSON-file-backed storage implementation for YasinFeed.
    Stores FeedSource and Article data inside a single structured JSON file.
    Uses atomic writes to ensure reliability.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        # Ensure parent directory exists
        file_dir = os.path.dirname(os.path.abspath(file_path))
        if file_dir:
            os.makedirs(file_dir, exist_ok=True)

        self.data: Dict[str, Any] = {
            "feed_sources": {},
            "articles": {}
        }
        self._load_data()

    def _load_data(self) -> None:
        """Loads data from the JSON file if it exists, otherwise initializes a new structure."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        loaded = json.loads(content)
                        if isinstance(loaded, dict):
                            self.data = {
                                "feed_sources": loaded.get("feed_sources", {}),
                                "articles": loaded.get("articles", {})
                            }
            except Exception:
                # Fallback to empty data structure
                self.data = {
                    "feed_sources": {},
                    "articles": {}
                }

    def _save_data(self) -> None:
        """Writes current data state atomically to the JSON file."""
        dir_name = os.path.dirname(self.file_path)
        # Create a temporary file in the same directory to perform atomic rename
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
            json.dump(self.data, tf, indent=2)
            tempname = tf.name
        try:
            os.replace(tempname, self.file_path)
        except Exception:
            if os.path.exists(tempname):
                os.remove(tempname)
            raise

    def save_feed_source(self, feed_source: FeedSource) -> None:
        """Saves or updates a FeedSource in the JSON store."""
        last_fetched_str = feed_source.last_fetched_at.isoformat() if feed_source.last_fetched_at else None
        self.data["feed_sources"][feed_source.id] = {
            "id": feed_source.id,
            "url": feed_source.url,
            "name": feed_source.name,
            "enabled": feed_source.enabled,
            "last_fetched_at": last_fetched_str
        }
        self._save_data()

    def get_feed_source(self, feed_source_id: str) -> Optional[FeedSource]:
        """Retrieves a FeedSource by its unique ID."""
        raw = self.data["feed_sources"].get(feed_source_id)
        if not raw:
            return None

        last_fetched_at = None
        if raw.get("last_fetched_at"):
            try:
                last_fetched_at = datetime.fromisoformat(raw["last_fetched_at"])
            except ValueError:
                pass

        return FeedSource(
            id=raw["id"],
            url=raw["url"],
            name=raw["name"],
            enabled=raw.get("enabled", True),
            last_fetched_at=last_fetched_at
        )

    def list_feed_sources(self) -> List[FeedSource]:
        """Lists all stored FeedSource entities."""
        sources = []
        for fid in self.data["feed_sources"]:
            src = self.get_feed_source(fid)
            if src:
                sources.append(src)
        return sources

    def save_article(self, article: Article) -> None:
        """Saves or updates an Article in the JSON store."""
        published_str = article.published_at.isoformat() if article.published_at else datetime.now().isoformat()
        self.data["articles"][article.id] = {
            "id": article.id,
            "source_id": article.source_id,
            "title": article.title,
            "content": article.content,
            "original_url": article.original_url,
            "published_at": published_str,
            "rewritten_content": article.rewritten_content,
            "rewrite_status": article.rewrite_status,
            "published_outputs": list(article.published_outputs or [])
        }
        self._save_data()

    def get_article(self, article_id: str) -> Optional[Article]:
        """Retrieves an Article by its unique ID."""
        raw = self.data["articles"].get(article_id)
        if not raw:
            return None

        try:
            published_at = datetime.fromisoformat(raw["published_at"])
        except ValueError:
            published_at = datetime.now()

        return Article(
            id=raw["id"],
            source_id=raw["source_id"],
            title=raw["title"],
            content=raw["content"],
            original_url=raw["original_url"],
            published_at=published_at,
            rewritten_content=raw.get("rewritten_content"),
            rewrite_status=raw.get("rewrite_status", "pending"),
            published_outputs=list(raw.get("published_outputs", []))
        )

    def list_articles(self) -> List[Article]:
        """Lists all stored Article entities."""
        articles = []
        for aid in self.data["articles"]:
            art = self.get_article(aid)
            if art:
                articles.append(art)
        return articles

    def close(self) -> None:
        """Saves state and closes backend cleanly."""
        self._save_data()
