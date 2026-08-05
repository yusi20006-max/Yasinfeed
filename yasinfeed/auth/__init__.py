import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from yasinfeed.engine import BaseModule
from yasinfeed.models import User, Session

def hash_password(password: str, salt: Optional[bytes] = None, iterations: int = 100000) -> Tuple[str, str]:
    """
    Hashes a password using PBKDF2 with SHA-256 and a random salt.
    Returns (password_hash_hex, salt_hex).
    """
    if salt is None:
        salt = os.urandom(16)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations
    )
    return pw_hash.hex(), salt.hex()

def verify_password(password: str, password_hash: str, salt_hex: str, iterations: int = 100000) -> bool:
    """
    Verifies a password against a hash and salt hex.
    """
    try:
        salt = bytes.fromhex(salt_hex)
        pw_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations
        )
        return pw_hash.hex() == password_hash
    except Exception:
        return False


class AuthModule(BaseModule):
    """
    Handles authentication, user management, and session validation.
    Integrates with the storage module to persist users and sessions.
    """

    def initialize(self) -> bool:
        self.logger.info("Initializing authentication module...")
        # Check config options if any
        auth_config = self.config.get("auth", {})
        self.token_expiry_hours = int(auth_config.get("token_expiry_hours", 24))
        self.min_password_length = int(auth_config.get("min_password_length", 8))
        self.iterations = int(auth_config.get("pbkdf2_iterations", 100000))
        return True

    def start(self) -> bool:
        self.logger.info("Authentication module started.")
        return True

    def stop(self) -> bool:
        self.logger.info("Authentication module stopped.")
        return True

    def _get_storage(self):
        storage = self.engine.modules.get("storage")
        if not storage:
            raise RuntimeError("Storage module not available in engine")
        return storage

    def register_user(self, username: str, password: str) -> User:
        """
        Registers a new user with secure password hashing.
        Raises ValueError for invalid inputs or duplicates.
        """
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")

        username = username.strip()
        if len(password) < self.min_password_length:
            raise ValueError(f"Password must be at least {self.min_password_length} characters long")

        storage = self._get_storage()

        # Check duplicate
        existing = storage.get_user_by_username(username)
        if existing:
            raise ValueError(f"Username '{username}' is already registered")

        # Create user
        user_id = str(uuid.uuid4())
        pw_hash, salt_hex = hash_password(password, iterations=self.iterations)
        created_at = datetime.now(timezone.utc)

        user = User(
            id=user_id,
            username=username,
            password_hash=pw_hash,
            salt=salt_hex,
            created_at=created_at
        )

        storage.save_user(user)
        self.logger.info("User registered successfully: %s", username)
        return user

    def login(self, username: str, password: str) -> Optional[Session]:
        """
        Authenticates user credentials and generates a high-entropy session token.
        Returns the Session object if successful, None otherwise.
        """
        if not username or not password:
            return None

        username = username.strip()
        storage = self._get_storage()
        user = storage.get_user_by_username(username)
        if not user:
            self.logger.warning("Authentication failed: user '%s' not found", username)
            return None

        # Verify password
        if not verify_password(password, user.password_hash, user.salt, iterations=self.iterations):
            self.logger.warning("Authentication failed: invalid password for '%s'", username)
            return None

        # Generate secure random token (64 hex characters / 256 bits)
        token = secrets.token_hex(32)
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(hours=self.token_expiry_hours)

        session = Session(
            token=token,
            user_id=user.id,
            expires_at=expires_at,
            created_at=created_at
        )

        storage.save_session(session)
        self.logger.info("User authenticated, session created: %s", username)
        return session

    def logout(self, token: str) -> bool:
        """
        Invalidates a session token. Returns True if successful.
        """
        if not token:
            return False

        storage = self._get_storage()
        session = storage.get_session(token)
        if session:
            storage.delete_session(token)
            self.logger.info("Session token invalidated.")
            return True
        return False

    def authenticate_token(self, token: str) -> Optional[User]:
        """
        Validates a session token and returns the corresponding User if valid and active.
        Returns None if token is invalid, expired, or user does not exist.
        """
        if not token:
            return None

        storage = self._get_storage()
        session = storage.get_session(token)
        if not session:
            return None

        # Check expiration
        now = datetime.now(timezone.utc)
        # Ensure comparison is timezone-aware
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if now > expires_at:
            self.logger.warning("Session token has expired.")
            storage.delete_session(token)
            return None

        # Retrieve user
        user = storage.get_user(session.user_id)
        if not user:
            self.logger.warning("User associated with session not found.")
            storage.delete_session(token)
            return None

        return user
