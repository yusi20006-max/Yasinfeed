from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from yasinfeed.engine import BaseModule

@dataclass
class FeedSource:
    id: str
    url: str
    name: str
    enabled: bool = True
    last_fetched_at: Optional[datetime] = None

@dataclass
class Article:
    id: str
    source_id: str
    title: str
    content: str
    original_url: str
    published_at: datetime
    rewritten_content: Optional[str] = None
    rewrite_status: str = "pending" # pending, completed, skipped
    published_outputs: List[str] = field(default_factory=list) # e.g. ["eitaa", "rss"]

class ModelsModule(BaseModule):
    """
    Manages data models and provides schemas for feed processing pipelines.
    """
    def initialize(self) -> bool:
        self.logger.info("Initializing models module...")
        return True

    def start(self) -> bool:
        self.logger.info("Models module started.")
        return True

    def stop(self) -> bool:
        self.logger.info("Models module stopped.")
        return True
