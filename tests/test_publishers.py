import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from yasinfeed.models.article import Article
from yasinfeed.publisher.pwa import PWAPublisher
from yasinfeed.publisher.rss import RSSPublisher


def article() -> Article:
    return Article(
        id="a1",
        source_id="bbc",
        title="خبر آزمایشی",
        content="متن اصلی خبر",
        original_url="https://example.com/news/a1",
        published_at=datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc),
        rewritten_content="متن بازنویسی‌شده",
        rewrite_status="completed",
        published_outputs=["eitaa"],
        pipeline_metadata={"category": "technology"},
    )


def pipeline_item() -> dict:
    return {
        "id": "dict-1",
        "source_id": "bbc",
        "title": "خبر از مسیر pipeline",
        "content": "متن اصلی",
        "url": "https://example.com/news/dict-1",
        "published_at": datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc),
    }


def test_pwa_publishes_json(tmp_path):
    path = tmp_path / "pwa" / "feed.json"
    publisher = PWAPublisher(str(path))

    result = publisher.publish([article()])

    assert result == str(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["version"] == "1.0"
    assert payload["count"] == 1
    assert payload["items"][0]["title"] == "خبر آزمایشی"
    assert payload["items"][0]["content"] == "متن بازنویسی‌شده"
    assert payload["items"][0]["url"] == "https://example.com/news/a1"


def test_rss_publishes_rss2(tmp_path):
    path = tmp_path / "rss" / "feed.xml"
    publisher = RSSPublisher(
        str(path),
        title="YasinFeed Test",
        link="https://example.com/feed",
        description="test feed",
    )

    result = publisher.publish([article()])

    assert result == str(path)
    root = ET.fromstring(path.read_bytes())
    assert root.tag == "rss"
    assert root.attrib["version"] == "2.0"
    channel = root.find("channel")
    assert channel is not None
    assert channel.findtext("title") == "YasinFeed Test"
    item = channel.find("item")
    assert item is not None
    assert item.findtext("title") == "خبر آزمایشی"
    assert item.findtext("description") == "متن بازنویسی‌شده"
    assert item.findtext("link") == "https://example.com/news/a1"
    assert item.find("guid") is not None


def test_publishers_accept_pipeline_dictionaries(tmp_path):
    pwa_path = tmp_path / "pwa.json"
    rss_path = tmp_path / "feed.xml"

    PWAPublisher(str(pwa_path)).publish([pipeline_item()])
    RSSPublisher(str(rss_path)).publish([pipeline_item()])

    pwa = json.loads(pwa_path.read_text(encoding="utf-8"))
    rss = ET.fromstring(rss_path.read_bytes())
    rss_item = rss.find("channel/item")

    assert pwa["items"][0]["title"] == "خبر از مسیر pipeline"
    assert pwa["items"][0]["url"] == "https://example.com/news/dict-1"
    assert rss_item is not None
    assert rss_item.findtext("title") == "خبر از مسیر pipeline"
    assert rss_item.findtext("link") == "https://example.com/news/dict-1"


def test_publishers_write_empty_valid_feeds(tmp_path):
    pwa_path = tmp_path / "pwa.json"
    rss_path = tmp_path / "feed.xml"

    PWAPublisher(str(pwa_path)).publish([])
    RSSPublisher(str(rss_path)).publish([])

    assert json.loads(pwa_path.read_text(encoding="utf-8"))["count"] == 0
    assert ET.fromstring(rss_path.read_bytes()).find("channel") is not None
