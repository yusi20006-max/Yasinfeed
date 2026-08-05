import os
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from yasinfeed.models import FeedSource, Article
from yasinfeed.database.base import BaseDatabaseProvider, DatabaseConfigurationError, DatabaseConnectionError


class SQLiteDatabaseProvider(BaseDatabaseProvider):
    """
    SQLite database provider implementation for YasinFeed.
    Fully compatible with Termux and standard Linux environments.
    """

    def validate_config(self) -> None:
        if not self.config or "path" not in self.config:
            raise DatabaseConfigurationError("SQLite configuration must specify a database 'path'.")

    def connect(self) -> None:
        db_path = self.config["path"]
        # Ensure parent directory exists
        db_dir = os.path.dirname(os.path.abspath(db_path))
        if db_dir:
            try:
                os.makedirs(db_dir, exist_ok=True)
            except Exception as e:
                raise DatabaseConnectionError(f"Failed to create directory for database: {e}")

        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._create_tables()
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Failed to connect to SQLite database at {db_path}: {e}")

    def _create_tables(self) -> None:
        """Creates tables for FeedSource and Article if they don't exist."""
        cursor = self.conn.cursor()

        # Table for FeedSource
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feed_sources (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                name TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                last_fetched_at TEXT
            )
        """)

        # Table for Article
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                original_url TEXT NOT NULL,
                published_at TEXT NOT NULL,
                rewritten_content TEXT,
                rewrite_status TEXT NOT NULL DEFAULT 'pending',
                published_outputs TEXT NOT NULL DEFAULT '[]'
            )
        """)

        self.conn.commit()

    def save_feed_source(self, feed_source: FeedSource) -> None:
        """Saves or updates a FeedSource using UPSERT semantics."""
        cursor = self.conn.cursor()
        last_fetched_str = feed_source.last_fetched_at.isoformat() if feed_source.last_fetched_at else None
        enabled_int = 1 if feed_source.enabled else 0

        cursor.execute("""
            INSERT INTO feed_sources (id, url, name, enabled, last_fetched_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                url = excluded.url,
                name = excluded.name,
                enabled = excluded.enabled,
                last_fetched_at = excluded.last_fetched_at
        """, (feed_source.id, feed_source.url, feed_source.name, enabled_int, last_fetched_str))
        self.conn.commit()

    def get_feed_source(self, feed_source_id: str) -> Optional[FeedSource]:
        """Retrieves a FeedSource by its unique ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, url, name, enabled, last_fetched_at FROM feed_sources WHERE id = ?", (feed_source_id,))
        row = cursor.fetchone()
        if not row:
            return None

        last_fetched_at = None
        if row["last_fetched_at"]:
            try:
                last_fetched_at = datetime.fromisoformat(row["last_fetched_at"])
            except ValueError:
                pass

        return FeedSource(
            id=row["id"],
            url=row["url"],
            name=row["name"],
            enabled=bool(row["enabled"]),
            last_fetched_at=last_fetched_at
        )

    def list_feed_sources(self) -> List[FeedSource]:
        """Lists all stored FeedSource entities."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, url, name, enabled, last_fetched_at FROM feed_sources")
        rows = cursor.fetchall()
        sources = []
        for row in rows:
            last_fetched_at = None
            if row["last_fetched_at"]:
                try:
                    last_fetched_at = datetime.fromisoformat(row["last_fetched_at"])
                except ValueError:
                    pass
            sources.append(FeedSource(
                id=row["id"],
                url=row["url"],
                name=row["name"],
                enabled=bool(row["enabled"]),
                last_fetched_at=last_fetched_at
            ))
        return sources

    def save_article(self, article: Article) -> None:
        """Saves or updates an Article using UPSERT semantics."""
        cursor = self.conn.cursor()
        published_str = article.published_at.isoformat() if article.published_at else datetime.now().isoformat()
        published_outputs_json = json.dumps(article.published_outputs or [])

        cursor.execute("""
            INSERT INTO articles (id, source_id, title, content, original_url, published_at, rewritten_content, rewrite_status, published_outputs)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                source_id = excluded.source_id,
                title = excluded.title,
                content = excluded.content,
                original_url = excluded.original_url,
                published_at = excluded.published_at,
                rewritten_content = excluded.rewritten_content,
                rewrite_status = excluded.rewrite_status,
                published_outputs = excluded.published_outputs
        """, (
            article.id,
            article.source_id,
            article.title,
            article.content,
            article.original_url,
            published_str,
            article.rewritten_content,
            article.rewrite_status,
            published_outputs_json
        ))
        self.conn.commit()

    def get_article(self, article_id: str) -> Optional[Article]:
        """Retrieves an Article by its unique ID."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, source_id, title, content, original_url, published_at, rewritten_content, rewrite_status, published_outputs
            FROM articles WHERE id = ?
        """, (article_id,))
        row = cursor.fetchone()
        if not row:
            return None

        try:
            published_at = datetime.fromisoformat(row["published_at"])
        except ValueError:
            published_at = datetime.now()

        try:
            published_outputs = json.loads(row["published_outputs"])
        except (ValueError, TypeError):
            published_outputs = []

        return Article(
            id=row["id"],
            source_id=row["source_id"],
            title=row["title"],
            content=row["content"],
            original_url=row["original_url"],
            published_at=published_at,
            rewritten_content=row["rewritten_content"],
            rewrite_status=row["rewrite_status"],
            published_outputs=published_outputs
        )

    def list_articles(self) -> List[Article]:
        """Lists all stored Article entities."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, source_id, title, content, original_url, published_at, rewritten_content, rewrite_status, published_outputs
            FROM articles
        """)
        rows = cursor.fetchall()
        articles = []
        for row in rows:
            try:
                published_at = datetime.fromisoformat(row["published_at"])
            except ValueError:
                published_at = datetime.now()

            try:
                published_outputs = json.loads(row["published_outputs"])
            except (ValueError, TypeError):
                published_outputs = []

            articles.append(Article(
                id=row["id"],
                source_id=row["source_id"],
                title=row["title"],
                content=row["content"],
                original_url=row["original_url"],
                published_at=published_at,
                rewritten_content=row["rewritten_content"],
                rewrite_status=row["rewrite_status"],
                published_outputs=published_outputs
            ))
        return articles

    def close(self) -> None:
        """Closes the SQLite database connection gracefully."""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
