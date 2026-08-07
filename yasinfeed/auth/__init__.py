import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Set, Dict

from yasinfeed.engine import BaseModule
from yasinfeed.models import User, Session
from .apikey import APIKeyAuth


# Define role-to-permission mapping
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "admin": {
        "read:articles", "write:articles",
        "read:sources", "write:sources",
        "read:scheduler", "write:scheduler",
        "read:stats", "admin"
    },
    "viewer": {
        "read:articles", "read:stats"
    }
}


class AuthModule(BaseModule):

    def initialize(self) -> bool:
        self.logger.info("Auth initialized.")

        # Load admin API key from config
        admin_key = self.config.get("api", {}).get("security", {}).get("admin_api_key")
        self.api_key = APIKeyAuth(secret=admin_key)

        self.storage = self.engine.modules.get("storage")

        if not self.storage:
            self.logger.error("Storage module unavailable for Auth.")
            return False

        return True


    def _hash_password(self, password: str, salt: str = None):

        if salt is None:
            salt = secrets.token_hex(16)

        password_hash = hashlib.sha256(
            (salt + password).encode("utf-8")
        ).hexdigest()

        return password_hash, salt


    def register_user(self, username: str, password: str, role: str = "viewer"):

        if not username or not password:
            raise ValueError("Username and password required")

        existing = self.storage.get_user_by_username(username)

        if existing:
            raise ValueError("Username already exists")

        if role not in ROLE_PERMISSIONS:
            raise ValueError(f"Invalid role: {role}")

        password_hash, salt = self._hash_password(password)

        user = User(
            id=secrets.token_hex(8),
            username=username,
            password_hash=password_hash,
            salt=salt,
            created_at=datetime.now(),
            role=role
        )

        self.storage.save_user(user)

        return user


    def login(self, username: str, password: str):

        user = self.storage.get_user_by_username(username)

        if not user:
            return None


        password_hash, _ = self._hash_password(
            password,
            user.salt
        )

        if password_hash != user.password_hash:
            return None

        expiry_hours = self.config.get("api", {}).get("security", {}).get("token_expiry_hours", 24)

        session = Session(
            token=secrets.token_hex(32),
            user_id=user.id,
            expires_at=datetime.now() + timedelta(hours=expiry_hours),
            created_at=datetime.now()
        )

        self.storage.save_session(session)

        return session


    def authenticate_token(self, token: str):

        session = self.storage.get_session(token)

        if not session:
            return None


        if session.expires_at and session.expires_at < datetime.now():
            self.storage.delete_session(token)
            return None


        return self.storage.get_user(session.user_id)


    def validate_api_key(self, key: str) -> bool:
        if not key:
            return False
        return self.api_key.validate(key)


    def has_permission(self, user: User, permission: str) -> bool:
        """
        Check if a user has a specific permission.
        """
        if not user:
            return False
        user_role = getattr(user, "role", "viewer") or "viewer"
        permissions = ROLE_PERMISSIONS.get(user_role, set())
        return permission in permissions


    def logout(self, token: str):

        self.storage.delete_session(token)

        return True
