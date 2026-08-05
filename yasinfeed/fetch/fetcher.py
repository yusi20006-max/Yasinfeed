import urllib.request
import feedparser


class FeedFetcher:

    def fetch(self, url):
        with urllib.request.urlopen(url, timeout=20) as r:
            data = r.read()

        feed = feedparser.parse(data)

        return feed
