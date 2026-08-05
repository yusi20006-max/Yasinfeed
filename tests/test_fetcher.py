import unittest
from unittest.mock import patch,MagicMock

from yasinfeed.fetch.fetcher import FeedFetcher

class TestFetcher(unittest.TestCase):

    @patch("urllib.request.urlopen")
    def test_fetch(self,m):
        obj=MagicMock()
        obj.read.return_value=b"<rss></rss>"
        obj.__enter__.return_value=obj
        m.return_value=obj

        f=FeedFetcher()
        data=f.fetch("http://test")

        self.assertIn("<rss>",data)

if __name__=="__main__":
    unittest.main()
