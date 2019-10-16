from . import BaseProvider
from app import db
from app.main.models import ContentItem, ContentTag


class RedditContentProvider(BaseProvider):
    def __init__(self, name):
        super(name)
        print(self.providerName)
    pass

    def getRandomItem(self, **kwargs):
        super(**kwargs)
        pass
    
    def execute(self, **kwargs):        
        pass
