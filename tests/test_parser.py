import unittest
from yasinfeed.fetch.parser import RSSParser

XML="""
<rss>
 <channel>
  <item>
   <title>News 1</title>
   <link>https://test.com/1</link>
   <description>Body</description>
  </item>
 </channel>
</rss>
"""

class TestParser(unittest.TestCase):

    def test_parse(self):
        parser=RSSParser()
        items=parser.parse(XML)

        self.assertEqual(len(items),1)
        self.assertEqual(items[0].title,"News 1")

if __name__=="__main__":
    unittest.main()
