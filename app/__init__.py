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
import redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Bot
#from flask_caching import Cache


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

log = logging.getLogger(__name__)

#logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

app = Flask(__name__)

app.config.from_object(Config)

db = SQLAlchemy(app)

migrate = Migrate(app, db)

bot = telebot.TeleBot(app.config['BOT_API_KEY'],threaded=False, skip_pending=True)
distracto_bot = Bot(token=app.config['DISTRACTOBOT_API_KEY'])

#flask mail
mail = Mail(app)

#cache

#cache = Cache(app)

#redis
redis_instance = redis.Redis(host=app.config['REDIS_SERVER'], port=app.config['REDIS_PORT'], password=app.config['REDIS_PASSWORD'])

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

from app.auth.routes import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

from app.main.routes import main as main_blueprint
app.register_blueprint(main_blueprint)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

from app.auth.models import User, Role

#set flask-security
from flask_security import Security, SQLAlchemyUserDatastore, login_required
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
app.security = Security(app, user_datastore)



#admin
from app.auth.modelviews import SecurityModelView
admin = Admin(app, name='tbot', template_mode='bootstrap3')
admin.add_view(SecurityModelView(User, db.session))
admin.add_view(SecurityModelView(Role, db.session))

#tasks
from app.tasks import process_shareprice_data
from app.distractobottasks import send_content

#bot handlers
from app.botcontrol import handlers


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

