import urllib.request

class FeedFetcher:

    def fetch(self,url):
        with urllib.request.urlopen(url,timeout=20) as r:
            return r.read().decode("utf-8")
