
from app import app
import os
from celery.schedules import crontab

class CeleryConfig(object):
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
    CELERY_TIME_ZONE = os.getenv('CELERY_TIME_ZONE'),
    CELERY_ENABLE_UTC = os.getenv('CELERY_ENABLE_UTC')
    CELERYBEAT_SCHEDULE = {          
        'send_to_subscribers_on_distractobot': {
            'task': 'app.distractobottasks.send_content',
            'schedule': crontab(minute="0", hour="6-21", day_of_week="mon,tue,wed,thu,fri")
        },
        'send_to_channels_on_distractobot': {
            'task': 'app.distractobottasks.send_channel_content',
            'schedule': crontab(hour="0,2,4,6,8,10,12,14,16,18,20,22", day_of_week="mon,tue,wed,thu,fri,sat")
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
