import praw
import os
from dotenv import load_dotenv
load_dotenv(verbose=True)

REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_USERNAME = os.getenv('REDDIT_USERNAME')
REDDIT_PASSWORD = os.getenv('REDDIT_PASSWORD')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')
reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID, client_secret=REDDIT_CLIENT_SECRET,
                     password=REDDIT_PASSWORD, username=REDDIT_USERNAME, user_agent=REDDIT_USER_AGENT)
