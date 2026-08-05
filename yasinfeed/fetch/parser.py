import xml.etree.ElementTree as ET
from datetime import datetime

class FeedItem:
    def __init__(self,title="",link="",content="",published_at=None):
        self.title=title
        self.link=link
        self.content=content
        self.published_at=published_at or datetime.utcnow()

class RSSParser:

    def parse(self, xml_text:str):
        root=ET.fromstring(xml_text)

        items=[]

        for item in root.findall(".//item"):
            items.append(
                FeedItem(
                    title=item.findtext("title",""),
                    link=item.findtext("link",""),
                    content=item.findtext("description",""),
                )
            )

        return items
