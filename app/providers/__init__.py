
class BaseProvider:
    def __init__(self, providerName, providerId):
        self.providerName = providerName
        self.providerId = providerId
    
    def getRandomItem(self, **kwargs):
        raise NotImplementedError()
    
    def execute(self, **kwargs):
        raise NotImplementedError()