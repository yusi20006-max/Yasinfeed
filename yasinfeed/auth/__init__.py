import hashlib
import secrets
from datetime import datetime, timedelta

from yasinfeed.engine import BaseModule
from yasinfeed.models import User, Session

from .apikey import APIKeyAuth


class AuthModule(BaseModule):

    def initialize(self):
        self.logger.info("Auth initialized.")

        self.api_key = APIKeyAuth()

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


    def register_user(self, username: str, password: str):

        if not username or not password:
            raise ValueError("Username and password required")

        existing = self.storage.get_user_by_username(username)

        if existing:
            raise ValueError("Username already exists")


        password_hash, salt = self._hash_password(password)

        user = User(
            id=secrets.token_hex(8),
            username=username,
            password_hash=password_hash,
            salt=salt,
            created_at=datetime.now()
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


        session = Session(
            token=secrets.token_hex(32),
            user_id=user.id,
            expires_at=datetime.now() + timedelta(hours=24),
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


    def logout(self, token: str):

        self.storage.delete_session(token)

        return True
