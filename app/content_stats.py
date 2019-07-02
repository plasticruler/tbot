from tasks import redis_instance
from datetime import datetime

class ContentStats:
    _timeformat = '%Y-%m-%d %H:%M:%S'
    @staticmethod
    def set_next_sent(chat_id):        
        n = datetime.now()  + datetime.timedelta(minutes=10)
        redis_instance.set('{}-nexttime'.format(chat_id), n.strftime(_timeformat))
