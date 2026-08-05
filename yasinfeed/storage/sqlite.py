from typing import Optional, List
from yasinfeed.models import FeedSource, Article, User, Session
from yasinfeed.storage.base import StorageBackend
from yasinfeed.database.factory import create_db_provider


class SQLiteStorage(StorageBackend):
    """
    SQLite-backed storage implementation for YasinFeed.
    Delegates database operations to the modular database layer.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        # Ensure parent directory exists
        db_dir = os.path.dirname(os.path.abspath(db_path))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

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

        # Table for User
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Table for Session
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        self.conn.commit()

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

    def save_user(self, user: User) -> None:
        """Saves or updates a User using UPSERT semantics."""
        cursor = self.conn.cursor()
        created_str = user.created_at.isoformat() if user.created_at else datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO users (id, username, password_hash, salt, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                username = excluded.username,
                password_hash = excluded.password_hash,
                salt = excluded.salt,
                created_at = excluded.created_at
        """, (user.id, user.username, user.password_hash, user.salt, created_str))
        self.conn.commit()

    def get_user(self, user_id: str) -> Optional[User]:
        """Retrieves a User by their unique ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, username, password_hash, salt, created_at FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return None

        try:
            created_at = datetime.fromisoformat(row["created_at"])
        except ValueError:
            created_at = datetime.now()

        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            salt=row["salt"],
            created_at=created_at
        )

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieves a User by their unique username."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, username, password_hash, salt, created_at FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if not row:
            return None

        try:
            created_at = datetime.fromisoformat(row["created_at"])
        except ValueError:
            created_at = datetime.now()

        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            salt=row["salt"],
            created_at=created_at
        )

    def list_users(self) -> List[User]:
        """Lists all stored User entities."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, username, password_hash, salt, created_at FROM users")
        rows = cursor.fetchall()
        users = []
        for row in rows:
            try:
                created_at = datetime.fromisoformat(row["created_at"])
            except ValueError:
                created_at = datetime.now()

            users.append(User(
                id=row["id"],
                username=row["username"],
                password_hash=row["password_hash"],
                salt=row["salt"],
                created_at=created_at
            ))
        return users

    def save_session(self, session: Session) -> None:
        """Saves or updates a Session using UPSERT semantics."""
        cursor = self.conn.cursor()
        created_str = session.created_at.isoformat() if session.created_at else datetime.now().isoformat()
        expires_str = session.expires_at.isoformat() if session.expires_at else datetime.now().isoformat()
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
        """Retrieves a Session by its unique token."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT token, user_id, expires_at, created_at FROM sessions WHERE token = ?", (token,))
        row = cursor.fetchone()
        if not row:
            return None

        try:
            created_at = datetime.fromisoformat(row["created_at"])
        except ValueError:
            created_at = datetime.now()

        try:
            expires_at = datetime.fromisoformat(row["expires_at"])
        except ValueError:
            expires_at = datetime.now()

        return Session(
            token=row["token"],
            user_id=row["user_id"],
            expires_at=expires_at,
            created_at=created_at
        )

    def delete_session(self, token: str) -> None:
        """Deletes/invalidates a Session by its token."""
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
            try:
                created_at = datetime.fromisoformat(row["created_at"])
            except ValueError:
                created_at = datetime.now()

            try:
                expires_at = datetime.fromisoformat(row["expires_at"])
            except ValueError:
                expires_at = datetime.now()

            sessions.append(Session(
                token=row["token"],
                user_id=row["user_id"],
                expires_at=expires_at,
                created_at=created_at
            ))
        return sessions

    def close(self) -> None:
        """Closes any open database connections gracefully."""
        self.provider.close()
