# coding: utf-8
import sys
import os
from dotenv import load_dotenv


load_dotenv(verbose=True)

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
    


class ProductionConfig(Config):
    DEBUG = False
    DEVELOPMENT = False
