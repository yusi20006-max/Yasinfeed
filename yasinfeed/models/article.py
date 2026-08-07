from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass
class Article:
    id: str
    source_id: str
    title: str
    content: str
    original_url: str
    published_at: datetime
    rewritten_content: Optional[str] = None
    rewrite_status: str = "pending"
    published_outputs: List[str] = field(default_factory=list)
    pipeline_metadata: Dict[str, Any] = field(default_factory=dict)
