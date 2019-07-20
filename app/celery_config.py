

from app.main.models import Key, KeyValueEntry
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
        'send_content_to_subscribers': {
            'task': 'app.tasks.send_content_to_subscribers',
            'schedule': crontab(day_of_week="mon,tue,wed,thu,fri,sat", minute="1", hour="6-18")
        },
        'download-share-data': {
            'task': 'app.tasks.download_share_prices',
            'schedule': crontab(minute="*/15", hour="7-16", day_of_week="mon,tue,wed,thu,fri")
        },
        'process-share-data': {
            'task': 'app.tasks.process_shareprice_data',
            'schedule': crontab(minute="*/20", hour="7-16", day_of_week="mon,tue,wed,thu,fri")
        }
    }
