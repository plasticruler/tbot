
from app.main.models import ContentItem, ContentTag
from app import db, log

class ContentCreatoryFactor:            
    pass

class BaseContentItemCreator:
    def __init__(self, providerName, providerId):
        self.providerName = providerName
        self.providerId = providerId
        self.contentItem = ContentItem()

    def GetValueFromConfig(self, key, defaultValue=None, raiseException=False):
        if key not in self.contentargs:
            if raiseException:
                raise ValueError(f"Argument {key} expected in GetContent.")
            else:
                return defaultValue
        else:
            return self.contentargs[key]

    def SetContentTags(self, *tags):
        self.contentItem.content_tags = [ContentTag.find_or_create_tag(tag) for tag in tags]

    def SaveItem(self):
        self.contentItem.save_to_db()
        self.contentItem = ContentItem()
    def ValidateArgs(self, *args):
        for k in args:
            self.GetValueFromConfig(k, raiseException=True)

    def GetContent(self, **kwargs):
        self.contentargs = kwargs        

class BaseContentProvider:
    def __init__(self, providerName, providerId):
        self.providerName = providerName
        self.providerId = providerId
    
    def getRandomItem(self, **kwargs):
        raise NotImplementedError()
    
    def execute(self, **kwargs):
        raise NotImplementedError()