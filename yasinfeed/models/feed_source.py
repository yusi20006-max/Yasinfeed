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
    # Multi Source Aggregation & Priority Management
    priority: int = 1
    weight: float = 1.0
    reliability_score: float = 1.0
    fetch_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_error: Optional[str] = None
