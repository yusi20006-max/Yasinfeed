import os
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from yasinfeed.models import FeedSource, Article, User, Session
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

        # Ensure multi-source aggregation columns exist (backward compatibility migration)
        for col_name, col_type, default_val in [
            ("priority", "INTEGER", "1"),
            ("weight", "REAL", "1.0"),
            ("reliability_score", "REAL", "1.0"),
            ("fetch_count", "INTEGER", "0"),
            ("success_count", "INTEGER", "0"),
            ("failure_count", "INTEGER", "0"),
            ("last_error", "TEXT", "NULL")
        ]:
            try:
                cursor.execute(f"ALTER TABLE feed_sources ADD COLUMN {col_name} {col_type} DEFAULT {default_val}")
            except sqlite3.OperationalError:
                pass  # column already exists

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

        # Table for User
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT DEFAULT '',
                salt TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'viewer'")
        except sqlite3.OperationalError:
            pass

        # Table for Session
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at TEXT,
                created_at TEXT
            )
        """)

        self.conn.commit()

    def save_feed_source(self, feed_source: FeedSource) -> None:
        """Saves or updates a FeedSource using UPSERT semantics."""
        cursor = self.conn.cursor()
        last_fetched_str = feed_source.last_fetched_at.isoformat() if feed_source.last_fetched_at else None
        enabled_int = 1 if feed_source.enabled else 0

        cursor.execute("""
            INSERT INTO feed_sources (id, url, name, enabled, last_fetched_at, priority, weight, reliability_score, fetch_count, success_count, failure_count, last_error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                url = excluded.url,
                name = excluded.name,
                enabled = excluded.enabled,
                last_fetched_at = excluded.last_fetched_at,
                priority = excluded.priority,
                weight = excluded.weight,
                reliability_score = excluded.reliability_score,
                fetch_count = excluded.fetch_count,
                success_count = excluded.success_count,
                failure_count = excluded.failure_count,
                last_error = excluded.last_error
        """, (
            feed_source.id,
            feed_source.url,
            feed_source.name,
            enabled_int,
            last_fetched_str,
            getattr(feed_source, "priority", 1),
            getattr(feed_source, "weight", 1.0),
            getattr(feed_source, "reliability_score", 1.0),
            getattr(feed_source, "fetch_count", 0),
            getattr(feed_source, "success_count", 0),
            getattr(feed_source, "failure_count", 0),
            getattr(feed_source, "last_error", None)
        ))
        self.conn.commit()

    def get_feed_source(self, feed_source_id: str) -> Optional[FeedSource]:
        """Retrieves a FeedSource by its unique ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM feed_sources WHERE id = ?", (feed_source_id,))
        row = cursor.fetchone()
        if not row:
            return None

        last_fetched_at = None
        if row["last_fetched_at"]:
            try:
                last_fetched_at = datetime.fromisoformat(row["last_fetched_at"])
            except ValueError:
                pass

        keys = row.keys()
        return FeedSource(
            id=row["id"],
            url=row["url"],
            name=row["name"],
            enabled=bool(row["enabled"]),
            last_fetched_at=last_fetched_at,
            priority=row["priority"] if "priority" in keys else 1,
            weight=row["weight"] if "weight" in keys else 1.0,
            reliability_score=row["reliability_score"] if "reliability_score" in keys else 1.0,
            fetch_count=row["fetch_count"] if "fetch_count" in keys else 0,
            success_count=row["success_count"] if "success_count" in keys else 0,
            failure_count=row["failure_count"] if "failure_count" in keys else 0,
            last_error=row["last_error"] if "last_error" in keys else None
        )

    def list_feed_sources(self) -> List[FeedSource]:
        """Lists all stored FeedSource entities."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM feed_sources")
        rows = cursor.fetchall()
        sources = []
        for row in rows:
            last_fetched_at = None
            if row["last_fetched_at"]:
                try:
                    last_fetched_at = datetime.fromisoformat(row["last_fetched_at"])
                except ValueError:
                    pass
            keys = row.keys()
            sources.append(FeedSource(
                id=row["id"],
                url=row["url"],
                name=row["name"],
                enabled=bool(row["enabled"]),
                last_fetched_at=last_fetched_at,
                priority=row["priority"] if "priority" in keys else 1,
                weight=row["weight"] if "weight" in keys else 1.0,
                reliability_score=row["reliability_score"] if "reliability_score" in keys else 1.0,
                fetch_count=row["fetch_count"] if "fetch_count" in keys else 0,
                success_count=row["success_count"] if "success_count" in keys else 0,
                failure_count=row["failure_count"] if "failure_count" in keys else 0,
                last_error=row["last_error"] if "last_error" in keys else None
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

    def save_user(self, user: User) -> None:
        """Saves or updates a User using UPSERT semantics."""
        cursor = self.conn.cursor()
        created_str = user.created_at.isoformat() if getattr(user, "created_at", None) else datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO users (id, username, password_hash, salt, created_at, role)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                username = excluded.username,
                password_hash = excluded.password_hash,
                salt = excluded.salt,
                created_at = excluded.created_at,
                role = excluded.role
        """, (user.id, user.username, user.password_hash, user.salt, created_str, getattr(user, "role", "viewer")))
        self.conn.commit()

    def get_user(self, user_id: str) -> Optional[User]:
        """Retrieves a User by their unique ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return None

        created_at = None
        if row["created_at"]:
            try:
                created_at = datetime.fromisoformat(row["created_at"])
            except ValueError:
                pass

        keys = row.keys()
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            salt=row["salt"],
            created_at=created_at,
            role=row["role"] if "role" in keys else "viewer"
        )

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieves a User by their username."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if not row:
            return None

        created_at = None
        if row["created_at"]:
            try:
                created_at = datetime.fromisoformat(row["created_at"])
            except ValueError:
                pass

        keys = row.keys()
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            salt=row["salt"],
            created_at=created_at,
            role=row["role"] if "role" in keys else "viewer"
        )

    def list_users(self) -> List[User]:
        """Lists all stored User entities."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        users = []
        for row in rows:
            created_at = None
            if row["created_at"]:
                try:
                    created_at = datetime.fromisoformat(row["created_at"])
                except ValueError:
                    pass
            keys = row.keys()
            users.append(User(
                id=row["id"],
                username=row["username"],
                password_hash=row["password_hash"],
                salt=row["salt"],
                created_at=created_at,
                role=row["role"] if "role" in keys else "viewer"
            ))
        return users

    def save_session(self, session: Session) -> None:
        """Saves or updates a Session using UPSERT semantics."""
        cursor = self.conn.cursor()
        expires_str = session.expires_at.isoformat() if session.expires_at else None
        created_str = session.created_at.isoformat() if session.created_at else None

        cursor.execute("""
            INSERT INTO sessions (token, user_id, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(token) DO UPDATE SET
                user_id = excluded.user_id,
                expires_at = excluded.expires_at,
                created_at = excluded.created_at
        """, (session.token, session.user_id, expires_str, created_str))
        self.conn.commit()

    def get_session(self, token: str) -> Optional[Session]:
        """Retrieves a Session by its token."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT token, user_id, expires_at, created_at FROM sessions WHERE token = ?", (token,))
        row = cursor.fetchone()
        if not row:
            return None

        expires_at = None
        if row["expires_at"]:
            try:
                expires_at = datetime.fromisoformat(row["expires_at"])
            except ValueError:
                pass

        created_at = None
        if row["created_at"]:
            try:
                created_at = datetime.fromisoformat(row["created_at"])
            except ValueError:
                pass

        return Session(
            token=row["token"],
            user_id=row["user_id"],
            expires_at=expires_at,
            created_at=created_at
        )

    def delete_session(self, token: str) -> None:
        """Deletes a Session by its token."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        self.conn.commit()

    def list_sessions(self) -> List[Session]:
        """Lists all stored Session entities."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT token, user_id, expires_at, created_at FROM sessions")
        rows = cursor.fetchall()
        sessions = []
        for row in rows:
            expires_at = None
            if row["expires_at"]:
                try:
                    expires_at = datetime.fromisoformat(row["expires_at"])
                except ValueError:
                    pass

            created_at = None
            if row["created_at"]:
                try:
                    created_at = datetime.fromisoformat(row["created_at"])
                except ValueError:
                    pass

            sessions.append(Session(
                token=row["token"],
                user_id=row["user_id"],
                expires_at=expires_at,
                created_at=created_at
            ))
        return sessions

    def close(self) -> None:
        """Closes the SQLite database connection gracefully."""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
