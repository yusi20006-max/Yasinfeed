from .article import Article
from .feed_source import FeedSource

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from yasinfeed.engine import BaseModule


@dataclass
class User:
    id: str
    username: str
    password_hash: str = ""
    salt: str = ""
    created_at: Optional[datetime] = None


@dataclass
class Session:
    token: str
    user_id: str
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class ModelsModule(BaseModule):
    def initialize(self):
        self.logger.info("Models initialized.")
        return True
