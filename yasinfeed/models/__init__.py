from yasinfeed.engine import BaseModule
from .article import Article
from .feed_source import FeedSource

@dataclass
class User:
    id: str
    username: str
    password_hash: str
    salt: str
    created_at: datetime

@dataclass
class Session:
    token: str
    user_id: str
    expires_at: datetime
    created_at: datetime

class ModelsModule(BaseModule):
    def initialize(self):
        self.logger.info("Models initialized.")
        return True
