import unittest
from datetime import datetime, timezone

from yasinfeed.models.article import Article
from yasinfeed.models.feed_source import FeedSource

class TestModels(unittest.TestCase):

    def test_article(self):
        a = Article(
            id="1",
            source_id="rss",
            title="title",
            content="body",
            original_url="https://example.com",
            published_at=datetime.now(timezone.utc),
        )
        self.assertEqual(a.rewrite_status, "pending")

    def test_feed_source(self):
        s = FeedSource(
            id="1",
            name="Feed",
            url="https://example.com/rss.xml",
        )
        self.assertTrue(s.enabled)

if __name__ == "__main__":
    unittest.main()
