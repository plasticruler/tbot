import sys
import os
from dotenv import load_dotenv
from os.path import join, dirname

dotenv_path = join(dirname(__file__), '.env')

load_dotenv(dotenv_path, verbose=True)

class Config(object):
    CORS_ENABLED = True
    DEBUG = True
    DEVELOPMENT = True
    SECRET_KEY = os.getenv('SECRET_KEY', 'this-os-n1t-kep@d')
    BOT_API_KEY = os.getenv('BOT_API_KEY')
    BOT_SECRET = os.getenv('BOT_SECRET')
    BOT_HOST = os.getenv('BOT_HOST').format(BOT_SECRET)
    MARIADB_HOST = os.getenv('MARIADB_HOST')
    MARIADB_USER = os.getenv('MARIADB_USER')
    MARIADB_PASSWORD = os.getenv('MARIADB_PASSWORD')
    MARIADB_DATABASE = os.getenv('MARIADB_DATABASE')
    SQLALCHEMY_DATABASE_URI = 'mysql://{}:{}@{}/{}'.format(
        MARIADB_USER, MARIADB_PASSWORD, MARIADB_HOST, MARIADB_DATABASE)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = os.getenv('MAIL_PORT')
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL')    
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')    

    USER_APP_NAME = "tBot Admin"
    USER_ENABLE_EMAIL = False
    USER_ENABLE_USERNAME = False
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = "noreply@a20.co.za"     
    NOTIFICATIONS_RECIPIENT_EMAIL = os.getenv('NOTIFICATIONS_RECIPIENT_EMAIL')

    ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

    REDIS_SERVER = os.getenv('REDIS_SERVER')
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    REDIS_PORT = os.getenv('REDIS_PORT')
    ADMIN_EMAIL = os.getenv('NOTIFICATIONS_RECIPIENT_EMAIL')    

    DOWNLOAD_FOLDER = os.getenv('DOWNLOAD_FOLDER')

    FAMILY_GROUP = os.getenv('FAMILY_GROUP')

    HOST_LOCATION = os.getenv('HOST_LOCATION')
    WEB_FOLDER = os.getenv('WEB_FOLDER')

    REDDIT_USERNAME=os.getenv('REDDIT_USERNAME')
    REDDIT_PASSWORD=os.getenv('REDDIT_PASSWORD')
    REDDIT_CLIENT_SECRET=os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_CLIENT_ID=os.getenv('REDDIT_CLIENT_ID')
    REDDIT_USER_AGENT=os.getenv('REDDIT_USER_AGENT')



class ProductionConfig(Config):
    DEBUG = False
    DEVELOPMENT = False
