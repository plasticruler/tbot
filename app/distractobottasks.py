from __future__ import unicode_literals
import json
import os
import requests
import datetime
from app import app, make_celery, log, distracto_bot, mail
from app.main.models import ContentStats, UserSubscription, Tag, Bot_Quote
from app.auth.models import User
from app.tasks import send_email
import time
import datetime
import re
import traceback


celery = make_celery(app)

@celery.task
def send_content():
    active_chat_ids = [u.chat_id for u in User.query.filter(User.active==True, User.bot_id==1, User.chat_id.isnot(None), User.subscriptions_active==True)]
    for u in active_chat_ids: 
        try:       
            send_random_quote(u)
        except Exception as e:
            log.debug(traceback.format_exc())   

@celery.task
def send_email(to, subject, plaintextMessage, deletable=True):    
    subject = "{}".format(subject + " <deletable>" if deletable else subject)
    try:        
        receiver_email = to
        message = "Subject: {} \n\n {}".format(subject, plaintextMessage)        
        msg = mail.send_message(subject, body=plaintextMessage, sender=app.config['MAIL_DEFAULT_SENDER'], recipients=to.split(','))
        log.debug("Email with subject '{}' sent to {}.".format(subject, to))
    except Exception as e:
        log.debug(e)            

@celery.task
def send_random_quote(chat_id):
    # based on the chat_id, we need to get a random quote from users subscribed items
    user = User.find_by_chatid(chat_id)    
    # get user subscriptions
    subs = UserSubscription.get_by_user(user.id)
    taglist = [t.content.value for t in subs]
    quote = Bot_Quote.return_random_by_tags(taglist)    
    if quote is None:
        distracto_bot.send_message(chat_id=chat_id, text="You have no subscriptions. Suspending your account.")
        user.subscriptions_active = False
        user.save_to_db()
        return
    payload = None
    try:
        payload = json.loads(quote.text)
        log.debug(payload)
        url = payload['url']            
    except ValueError:
        distracto_bot.send_message(chat_id=ADMIN_CHAT_ID, text="{} ({})".format(quote.text, quote.id)) #plaintext
        return

    if has_content_moved(url):
            send_random_quote(chat_id)
            return

    if is_video_related_post(payload):
        # is gfycat
        if 'media' in payload and payload['media'] is not None:            
            if 'type' in payload['media']:
                if payload['media']['type'] == 'gfycat':
                    url = payload['media']['oembed']['thumbnail_url']
            if not payload['is_reddit_media_domain'] and payload['media'] is None:
                url = payload['url']
            if 'reddit_video' in payload['media']:
                if payload['media']['reddit_video']['is_gif']:
                    url = payload['media']['reddit_video']['fallback_url']        
        try:                    
            if ("nsfw" not in payload['title']):
                distracto_bot.send_video(chat_id, url, caption="{} (https://reddit.com/{})".format(payload['title'], payload['id']))
                ContentStats.add_statistic(user, quote)
            else:
                send_random_quote(chat_id)
        except Exception as e:          
            send_random_quote(chat_id)        
        return
    try:        
        distracto_bot.send_photo(chat_id, url, caption="{} (http://reddit.com/{})".format(payload['title'], payload['id']))
        ContentStats.add_statistic(user, quote)
    except Exception as e:
        send_random_quote(chat_id)        

###############################################################################

def is_video_related_post(payload):
    url = payload['url']
    if 'reddit_media_domain' in payload:
        pattern = 'https://v.redd.it/[a-zA-Z0-9]{13}'
        if re.match(pattern, url):
            return True
    if 'media' in payload:
        media = payload['media']
        if media is not None and 'reddit_video' in media:
            return 'reddit_video' in media
    if 'http://v.redd.it' in url or 'gfycat.com' in url or url.endswith('mp4') or url.endswith('.gif') or 'imgur.com' in url:
        return True
    return False

def has_content_moved(url):  # ignore when you are redirected to reddit
    r = requests.head(url, allow_redirects=False) #only request header
    return r.status_code == 302


##################################################################################

