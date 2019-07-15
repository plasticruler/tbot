import click

from flask import Flask, request
from flask_cors import CORS
from flask_restful.utils import cors
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_migrate import Migrate
from flask.cli import with_appcontext
from flask_login import LoginManager, user_logged_in

from celery import Celery
from bs4 import BeautifulSoup
import logging
import os
import sys
import datetime
import matplotlib.pyplot as plt

from app.config import Config
import json
import telebot


logging.basicConfig(level=logging.DEBUG)
logging.getLogger('flask_cors').level = logging.DEBUG

log = logging.getLogger(__name__)

app = Flask(__name__)

api = Api(app, decorators=[cors.crossdomain(origin='*')])
app.config.from_object(Config)

db = SQLAlchemy(app)

migrate = Migrate(app, db)


BOT_API_KEY = app.config['BOT_API_KEY']
BOT_HOST = app.config['BOT_HOST']
BOT_SECRET = app.config['BOT_SECRET']

bot = telebot.TeleBot(BOT_API_KEY, threaded=False, skip_pending=True)

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

from .auth_routes import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

from .main_routes import main as main_blueprint
app.register_blueprint(main_blueprint)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)


from app import bothandlers, tasks, models

from app.models import EquityInstrument, Key, KeyValueEntry, EquityPrice, User
from app.tasks import download_file, download_share_prices, update_multiple_reddit_subs_using_payload, process_shareprice_data


#set loginmanager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# register api resources
#api.add_resource(TagResource, '/api/1.0/tag')
#api.add_resource(QuoteResource, '/api/1.0/quote')
#api.add_resource(EquityInstrumentResource, '/api/1.0/equityinstrument/')
#api.add_resource(TrackedInstrumentResource, '/api/1.0/trackedinstrument/')

#########

# cli click commands

@app.cli.command()
@click.argument('url')
@click.argument('file_name')
@with_appcontext
def downloadfileusingtask(url, file_name):
    download_file(url, file_name)


@app.cli.command()
@with_appcontext
def downloadsharedatausingtask():
    download_share_prices()


@app.cli.command()
@with_appcontext
def processsharepricedata():
    process_shareprice_data()

@app.cli.command()
@click.argument('file_name')
@with_appcontext
def importinstruments(file_name):
    page_content = ''
    with open(file_name, 'r') as f:
        page_content = f.read()
    soup = BeautifulSoup(page_content, features='html5lib')
    tabs = soup.find_all('table')
    trs = tabs[1].find_all('tr')[1:]  # skip header
    for tr in trs:
        spans = tr.find_all('span')
        ei = EquityInstrument()
        ei.jse_code = spans[1].text.strip()
        ei.company_name = spans[0].text.strip()
        ei.save_to_db()


@app.cli.command()
@click.argument('file_name')
def importkeyvaluepairs(file_name):
    if not os.path.isfile(file_name):
        log.error('File does not exist. {}'.format(file_name))
    with open(file_name, 'r') as f:
        for line in f:
            if (len(line.strip())==0):
                continue
            k, v = line.split('=')
            k, v = k.strip(), v.strip()
            if KeyValueEntry.find_by_key_value(k, v) is not None or '=' not in line:
                continue
            key = Key.find_by_name(k)
            if (key is None):
                key = Key()
                key.name = k
                key.save_to_db()
            kv = KeyValueEntry()
            kv.key = key
            kv.value = v.strip()
            kv.save_to_db()
    log.info('Processing done.')

@app.cli.command()
@click.argument('url') 
def sendvideo(url):
    bot.send_video(os.getenv('ADMIN_CHAT_ID'), url)

@app.cli.command()
@click.argument('subredditname')
def importredditmediatargeted(subredditname):
    tasks.update_reddit_subs_using_payload.delay(subredditname,limit=1000)

@app.cli.command()
def sendrandomquote():
    ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
    tasks.send_random_quote(ADMIN_CHAT_ID)

@app.cli.command()
@click.argument('subredditname')
def importreddittitletargeted(subredditname):
    tasks.update_multiple_reddit_subs_using_title.delay(subredditname,limit=1000)


@app.cli.command()
@with_appcontext
def importredditcontent():
    reddits = KeyValueEntry.get_by_key('sr_media')
    for red in reddits:
        tasks.update_reddit_subs_using_payload.delay(red.value,limit=1000)
        log.info('Set task for {}'.format(red.value))
    reddits = KeyValueEntry.get_by_key('sr_title')
    for red in reddits:
        tasks.update_reddit_subs_from_title.delay(red.value,limit=500)
        log.info('Set task for {}'.format(red.value))


