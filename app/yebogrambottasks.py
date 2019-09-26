import json
import os
import requests
import emoji
import datetime
from app import app, make_celery, log, mail
from app.yebogram.models import WorkItem
from app.auth.models import User
import time
import random
import re
import traceback
from app.utils import get_md5
from app import log, db, yebogrambot
import telegram
from MySQLdb._exceptions import IntegrityError
from sqlalchemy.exc import InvalidRequestError
from app.commontasks import send_system_message

celery = make_celery(app)

@celery.task
def check_work(media_id, userid):
    pass