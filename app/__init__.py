import click

from flask import Flask, request 

from flask_sqlalchemy import SQLAlchemy

from flask_migrate import Migrate
from flask.cli import with_appcontext
from flask_login import LoginManager, user_logged_in


from celery import Celery

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_mail import Mail

import logging
import os
import sys
import datetime
import matplotlib.pyplot as plt

from app.config import Config
import json
import telebot
import telegram
import redis
import requests

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Bot
from flask_session import Session
#from flask_caching import Cache


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

log = logging.getLogger(__name__)

#logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

app = Flask(__name__)

app.config.from_object(Config)

db = SQLAlchemy(app)

migrate = Migrate(app, db)

bot = telebot.TeleBot(app.config['BOT_API_KEY'],threaded=False, skip_pending=True)

distractobot = telegram.Bot(token=app.config['DISTRACTOBOT_API_KEY']) 
yebogrambot = telegram.Bot(token=app.config['YEBOGRAMBOT_API_KEY'])

#flask mail
mail = Mail(app)

#redis
redis_instance = redis.Redis(host=app.config['REDIS_SERVER'], port=app.config['REDIS_PORT'], password=app.config['REDIS_PASSWORD'])

app.config['SESSION_REDIS'] = redis_instance
Session(app)

# celery

from app.celery_config import CeleryConfig
def make_celery(app):
    celery = Celery(app.import_name)
    celery.config_from_object(CeleryConfig)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery 

celery = make_celery(app)

from app.auth.routes import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

from app.main.routes import main as main_blueprint
app.register_blueprint(main_blueprint)

from app.backoffice.routes import backoffice as backoffice_blueprint
app.register_blueprint(backoffice_blueprint)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

from app.auth.models import User, Role

#set flask-security
from flask_security import Security, SQLAlchemyUserDatastore, login_required
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
app.security = Security(app, user_datastore)

#admin
#from app.auth.modelviews import SecurityModelView
#admin = Admin(app, name='tbot', template_mode='bootstrap3')
#admin.add_view(SecurityModelView(User, db.session))
#admin.add_view(SecurityModelView(Role, db.session))

#tasks
from app.tasks import process_shareprice_data


@login_manager.user_loader
def load_user(user_id):    
    return User.query.get(int(user_id))

@app.before_first_request
def create_user():
    db.create_all() 

# cli click commands
@app.cli.command()
@with_appcontext
def processsharepricedata():
    process_shareprice_data.delay()

import json
from app.auth.models import User
from app.main.models import UserSubscription
@app.cli.command()
@with_appcontext
def importusers():
    t = ""
    users = {}
    with open("/home/romeo/user_subs.json") as f:
        t = f.read()
        subs = json.loads(t)
    for user in subs:
        print(user)
        u = UserSubscription()
        u.user_id = user.get('user_id')
        u.keyvalue_entry_id = user.get('keyvalue_entry_id')        
        u.save_to_db()

from app.main.models import ContentItem
@app.cli.command()
@with_appcontext
def exportdata():
    url = "http://localhost:5000/api/ContentItems"
    for contentItem in ContentItem.query.all():
        d = {}
        d["title"] = contentItem.title
        d["data"] = contentItem.data
        d["contentProviderID"] = contentItem.contentprovider_id
        d["contentHash"] = contentItem.content_hash
        d["isDeleted"] = False
        d["id"] = contentItem.id
        response = requests.post(url, json=d)
        print(response.status_code, d["id"], d["title"])

from app.main.models import ContentItem
@app.cli.command()
@with_appcontext
def exporttagdata():
    url = "http://localhost:5000/api/ContentItemTags"
    for contentItem in ContentItem.query.limit(10).all():
        for t in contentItem.content_tags:            
            d = {}
            d["contentItemId"] = contentItem.title
            d["tag"] = t.name
            response = requests.post(url, json=d)
            print(response.status_code)
            
# cli click commands
@app.cli.command()
@click.argument("chatid")
@click.argument("message")
@with_appcontext
def sendmessage_db(chatid, message):
    print(chatid, message)
    distractobot.send_message(chatid, message)

from app.distractobottasks import update_reddit
@app.cli.command()
@click.argument("tag")
@with_appcontext
def refresh_reddit(tag):        
    update_reddit(tag, limit=100)
