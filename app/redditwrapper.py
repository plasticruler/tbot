import praw
import os
from app import app
reddit = praw.Reddit(client_id=app.config['REDDIT_CLIENT_ID'], client_secret=app.config['REDDIT_CLIENT_SECRET'],
                     password=app.config['REDDIT_PASSWORD'], username=app.config['REDDIT_USERNAME'], user_agent=app.config['REDDIT_USER_AGENT'])
