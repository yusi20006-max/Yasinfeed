"""Static JSON publisher for PWA consumers."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


class PWAPublisher:
    """Publish curated articles as an atomic, UTF-8 JSON datasource."""

    def __init__(self, output_path: str = "data/pwa/feed.json", *, base_url: str = "") -> None:
        self.output_path = Path(output_path)
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def _iso(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def _article(self, article: Any) -> dict[str, Any]:
        url = getattr(article, "original_url", "") or ""
        return {
            "id": getattr(article, "id", ""),
            "source_id": getattr(article, "source_id", ""),
            "title": getattr(article, "title", ""),
            "content": getattr(article, "rewritten_content", None) or getattr(article, "content", ""),
            "original_url": url,
            "url": url,
            "published_at": self._iso(getattr(article, "published_at", None)),
            "rewrite_status": getattr(article, "rewrite_status", "pending"),
            "published_outputs": list(getattr(article, "published_outputs", []) or []),
            "pipeline_metadata": dict(getattr(article, "pipeline_metadata", {}) or {}),
        }

    def render(self, articles: Iterable[Any]) -> dict[str, Any]:
        items = [self._article(article) for article in articles]
        return {
            "version": "1.0",
            "generated_at": datetime.now().astimezone().isoformat(),
            "count": len(items),
            "items": items,
        }

    def publish(self, articles: Iterable[Any]) -> str:
        """Write the PWA datasource atomically and return its path."""
        payload = self.render(articles)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{self.output_path.name}.",
            suffix=".tmp",
            dir=str(self.output_path.parent),
            text=True,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.output_path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

        return str(self.output_path)
