
from app.models import Key, KeyValueEntry
import os
from celery.schedules import crontab

def get_full_payload_reddits():
    reddits = KeyValueEntry.get_by_key('sr_media') 
    if reddits is None:
        reddits = []
    return ",".join([x.value for x in reddits])

def get_title_reddits():
    reddits = KeyValueEntry.get_by_key('sr_title')
    if reddits is None:
        reddits = [] 
    return ",".join([x.value for x in reddits])


class CeleryConfig(object):
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
    CELERY_TIME_ZONE = os.getenv('CELERY_TIME_ZONE'),
    CELERY_ENABLE_UTC = os.getenv('CELERY_ENABLE_UTC')
    CELERYBEAT_SCHEDULE = {
        'send-uptime-message': {
            'task': 'app.tasks.send_uptime_message',
            'schedule': crontab(hour="6,8,10,12,14,16,18", minute=1),  # UTC
        },
        'update-subreddits-by-payload': {
            'task': 'app.tasks.update_multiple_reddit_subs_using_payload',
            'schedule': crontab(minute=21, hour=20, day_of_month=26),
            'args': (get_full_payload_reddits(), 'month', 500)
        },
        'update-subreddits-by-title': {
            'task': 'app.tasks.update_multiple_reddit_subs_using_title',
            'schedule': crontab(minute=21, hour=20, day_of_month=26),
            'args': (get_title_reddits(), 'month', 500)
        },
        'download-share-data': {
            'task': 'app.tasks.download_share_prices',
            'schedule': crontab(minute="*/15", hour="7-16", day_of_week="mon,tue,wed,thu,fri")
        },
        'process-share-data': {
            'task': 'app.tasks.process_shareprice_data',
            'schedule': crontab(minute="1", hour="7-16", day_of_week="mon,tue,wed,thu,fri")
        }
    }
