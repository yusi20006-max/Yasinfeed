from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class FeedSource:
    id: str
    name: str
    url: str
    enabled: bool = True
    last_fetched_at: Optional[datetime] = None
