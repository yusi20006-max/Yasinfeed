"""RSS 2.0 publisher for YasinFeed."""

from __future__ import annotations

import os
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Any, Iterable


class RSSPublisher:
    """Publish curated articles as an atomic RSS 2.0 XML file."""

    def __init__(
        self,
        output_path: str = "data/rss/feed.xml",
        *,
        title: str = "YasinFeed",
        link: str = "http://127.0.0.1:8000/api/feed",
        description: str = "YasinFeed published news",
    ) -> None:
        self.output_path = Path(output_path)
        self.title = title
        self.link = link
        self.description = description

    @staticmethod
    def _published(value: Any) -> str:
        if isinstance(value, datetime):
            dt = value
        else:
            try:
                dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except (TypeError, ValueError):
                dt = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return format_datetime(dt.astimezone(timezone.utc), usegmt=True)

    def render(self, articles: Iterable[Any]) -> bytes:
        rss = ET.Element("rss", {"version": "2.0"})
        channel = ET.SubElement(rss, "channel")
        ET.SubElement(channel, "title").text = self.title
        ET.SubElement(channel, "link").text = self.link
        ET.SubElement(channel, "description").text = self.description
        ET.SubElement(channel, "lastBuildDate").text = format_datetime(
            datetime.now(timezone.utc), usegmt=True
        )

        for article in articles:
            item = ET.SubElement(channel, "item")
            title = getattr(article, "title", "") or ""
            url = getattr(article, "original_url", "") or ""
            content = getattr(article, "rewritten_content", None) or getattr(article, "content", "") or ""
            article_id = getattr(article, "id", "") or url

            ET.SubElement(item, "title").text = title
            ET.SubElement(item, "link").text = url
            ET.SubElement(item, "guid", {"isPermaLink": "false"}).text = str(article_id)
            ET.SubElement(item, "description").text = content
            ET.SubElement(item, "pubDate").text = self._published(
                getattr(article, "published_at", None)
            )

        return ET.tostring(rss, encoding="utf-8", xml_declaration=True)

    def publish(self, articles: Iterable[Any]) -> str:
        """Write RSS 2.0 XML atomically and return its path."""
        payload = self.render(articles)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{self.output_path.name}.",
            suffix=".tmp",
            dir=str(self.output_path.parent),
        )
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.output_path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

        return str(self.output_path)
