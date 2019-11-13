import hashlib
from datetime import datetime

from . import BaseContentItemCreator, BaseContentProvider
from app import db, log
from app.main.models import ContentItem, ContentTag
from app.redditwrapper import reddit
import requests

class Manager(BaseContentItemCreator):
    """
    A class to manage all things XKCD related
    """
    BASE_URL = f"https://xkcd.com/%s/info.0.json"
    TAGS = ['xkcd.com']

    def __init__(self):
        pass

    def CreateContent(self, count=None):
        """Get articles
        :param int count : The number of articles to extract
        """

        for idx in range(1, count+1):
            article = XKCDContent(article_num=idx)
            print(json.dumps(article.dump())

class XKCDContent:
    __slots__ = 'url', 'title', 'image', 'text', 'date', 'image', 'content_hash', 'tags'
    BASE_URL = "https://xkcd.com/{}/info.0.json"
    TAGS = ['xkcd.com']

    def __init__(self, article_num):
        self.url = self.BASE_URL.format(article_num)

        self.title = None
        self.image = None
        self.text = None
        self.date = None
        self.content_hash = None
        self.tags = self.TAGS

        self.extract()

    def parse_payload(self, payload):
        """Parses the payload for the extracted content
        """

        self.title = payload.get('safe_title')
        self.image = payload.get('img')
        self.text = payload.get('transcript')

        year = int(payload.get('year'))
        month = int(payload.get('month'))
        day = int(payload.get('day'))
        self.date = datetime(year=year, month=month, day=day)

        hashable_content = payload.get('num', None)
        if hashable_content:
            self.content_hash = hashlib.md5(str(hashable_content).encode('utf-8')).hexdigest()

    def extract(self):
        """Extracts the content from the XKCD server
        """
        try:
            response = requests.get(self.url)
            response.raise_for_status()

        except Exception as http_err:
            print(f'HTTP error occurred: {http_err}')
        except Exception as err:
            print(f'Other error occurred: {err}')

        self.parse_payload(response.json())

    def dump(self):
        """Dumps the extracted article
        """

        return {
            'title': self.title,
            'text': self.text,
            'image': self.image,
            'date': str(self.date),
            'content_hash': self.content_hash,
            'tags': self.tags
        }
class XKCDContentItemCreator(BaseContentItemCreator):
    def __init__(self):
        super().__init__("XKCD", 2)

    def GetContent(self, **kwargs):
        pass