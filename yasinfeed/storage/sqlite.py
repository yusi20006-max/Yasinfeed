from typing import Optional, List
from datetime import datetime
import sqlite3
import os

from yasinfeed.models import FeedSource, Article, User, Session
from yasinfeed.storage.base import StorageBackend


class SQLiteStorage(StorageBackend):
    """
    SQLite storage backend.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

        db_dir = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(db_dir, exist_ok=True)

        self.conn = sqlite3.connect(
            db_path,
            check_same_thread=False
        )

        self.conn.row_factory = sqlite3.Row

        self._create_tables()


    def _create_tables(self):

        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feed_sources (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
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


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            original_url TEXT NOT NULL,
            published_at TEXT NOT NULL,
            rewritten_content TEXT,
            rewrite_status TEXT DEFAULT 'pending',
            published_outputs TEXT DEFAULT '[]'
        )
        """)


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


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            expires_at TEXT,
            created_at TEXT
        )
        """)


        self.conn.commit()


    def save_feed_source(self, feed_source):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO feed_sources
            (id, name, url, enabled, last_fetched_at, priority, weight, reliability_score, fetch_count, success_count, failure_count, last_error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            url=excluded.url,
            enabled=excluded.enabled,
            last_fetched_at=excluded.last_fetched_at,
            priority=excluded.priority,
            weight=excluded.weight,
            reliability_score=excluded.reliability_score,
            fetch_count=excluded.fetch_count,
            success_count=excluded.success_count,
            failure_count=excluded.failure_count,
            last_error=excluded.last_error
            """,
            (
                feed_source.id,
                feed_source.name,
                feed_source.url,
                1 if feed_source.enabled else 0,
                feed_source.last_fetched_at.isoformat()
                if getattr(feed_source, "last_fetched_at", None)
                else None,
                getattr(feed_source, "priority", 1),
                getattr(feed_source, "weight", 1.0),
                getattr(feed_source, "reliability_score", 1.0),
                getattr(feed_source, "fetch_count", 0),
                getattr(feed_source, "success_count", 0),
                getattr(feed_source, "failure_count", 0),
                getattr(feed_source, "last_error", None)
            )
        )

        self.conn.commit()


    def get_feed_source(self, feed_source_id):
        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT * FROM feed_sources WHERE id=?",
            (feed_source_id,)
        )

        row = cursor.fetchone()

        if not row:
            return None

        last_fetched_at = None
        if "last_fetched_at" in row.keys() and row["last_fetched_at"]:
            try:
                last_fetched_at = datetime.fromisoformat(row["last_fetched_at"])
            except ValueError:
                pass

        keys = row.keys()
        return FeedSource(
            id=row["id"],
            name=row["name"],
            url=row["url"],
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


    def list_feed_sources(self):
        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT * FROM feed_sources"
        )

        rows = cursor.fetchall()

        sources = []
        for row in rows:
            last_fetched_at = None
            if "last_fetched_at" in row.keys() and row["last_fetched_at"]:
                try:
                    last_fetched_at = datetime.fromisoformat(row["last_fetched_at"])
                except ValueError:
                    pass
            keys = row.keys()
            sources.append(
                FeedSource(
                    id=row["id"],
                    name=row["name"],
                    url=row["url"],
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
            )
        return sources


    def save_article(self, article):
        import json

        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO articles
            (
                id,
                source_id,
                title,
                content,
                original_url,
                published_at,
                rewritten_content,
                rewrite_status,
                published_outputs
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            content=excluded.content,
            rewritten_content=excluded.rewritten_content,
            rewrite_status=excluded.rewrite_status,
            published_outputs=excluded.published_outputs
            """,
            (
                article.id,
                article.source_id,
                article.title,
                article.content,
                article.original_url,
                article.published_at.isoformat(),
                getattr(article, "rewritten_content", None),
                getattr(article, "rewrite_status", "pending"),
                json.dumps(
                    getattr(article, "published_outputs", [])
                )
            )
        )

        self.conn.commit()


    def get_article(self, article_id):
        import json

        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT * FROM articles WHERE id=?",
            (article_id,)
        )

        row = cursor.fetchone()

        if not row:
            return None

        return Article(
            id=row["id"],
            source_id=row["source_id"],
            title=row["title"],
            content=row["content"],
            original_url=row["original_url"],
            published_at=datetime.fromisoformat(row["published_at"]),
            rewritten_content=row["rewritten_content"],
            rewrite_status=row["rewrite_status"],
            published_outputs=json.loads(
                row["published_outputs"]
            )
        )


    def list_articles(self):
        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT * FROM articles"
        )

        rows = cursor.fetchall()

        return [
            self.get_article(row["id"])
            for row in rows
        ]


    def save_user(self, user):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO users
            (id, username, password_hash, salt, created_at, role)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
            username=excluded.username,
            password_hash=excluded.password_hash,
            salt=excluded.salt,
            created_at=excluded.created_at,
            role=excluded.role
            """,
            (
                user.id,
                user.username,
                user.password_hash,
                user.salt,
                user.created_at.isoformat()
                if getattr(user, "created_at", None)
                else datetime.now().isoformat(),
                getattr(user, "role", "viewer")
            )
        )

        self.conn.commit()


    def get_user(self, user_id):
        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE id=?",
            (user_id,)
        )

        row = cursor.fetchone()

        if not row:
            return None

        keys = row.keys()
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            salt=row["salt"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            role=row["role"] if "role" in keys else "viewer"
        )


    def get_user_by_username(self, username):
        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        row = cursor.fetchone()

        if not row:
            return None

        keys = row.keys()
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            salt=row["salt"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            role=row["role"] if "role" in keys else "viewer"
        )


    def list_users(self):
        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT * FROM users"
        )

        rows = cursor.fetchall()

        users = []
        for row in rows:
            keys = row.keys()
            users.append(
                User(
                    id=row["id"],
                    username=row["username"],
                    password_hash=row["password_hash"],
                    salt=row["salt"],
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                    role=row["role"] if "role" in keys else "viewer"
                )
            )
        return users


    def save_session(self, session):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO sessions
            (token, user_id, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(token) DO UPDATE SET
            user_id=excluded.user_id,
            expires_at=excluded.expires_at,
            created_at=excluded.created_at
            """,
            (
                session.token,
                session.user_id,
                session.expires_at.isoformat()
                if session.expires_at else None,
                session.created_at.isoformat()
                if session.created_at else None
            )
        )

        self.conn.commit()


    def get_session(self, token):
        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT * FROM sessions WHERE token=?",
            (token,)
        )

        row = cursor.fetchone()

        if not row:
            return None

        from datetime import datetime

        return Session(
            token=row["token"],
            user_id=row["user_id"],
            expires_at=datetime.fromisoformat(row["expires_at"])
            if row["expires_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"])
            if row["created_at"] else None
        )


    def delete_session(self, token):
        cursor = self.conn.cursor()

        cursor.execute(
            "DELETE FROM sessions WHERE token=?",
            (token,)
        )

        self.conn.commit()


    def list_sessions(self):
        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT * FROM sessions"
        )

        rows = cursor.fetchall()

        from datetime import datetime

        return [
            Session(
                token=row["token"],
                user_id=row["user_id"],
                expires_at=datetime.fromisoformat(row["expires_at"])
                if row["expires_at"] else None,
                created_at=datetime.fromisoformat(row["created_at"])
                if row["created_at"] else None
            )
            for row in rows
        ]


    def close(self):

        if hasattr(self, "conn"):
            self.conn.close()
