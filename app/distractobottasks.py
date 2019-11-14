from __future__ import unicode_literals

import json
import random
import traceback

import emoji
import requests
import telegram
from emoji import emojize
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app import app, make_celery
from app import log, distractobot
from app.auth.models import User
from app.commontasks import send_system_message
from app.main.models import UserSubscription, ContentItem, ContentTag, Notification, ContentItemStat
from app.redditwrapper import reddit
from app.utils import get_md5

celery = make_celery(app)

def getsubmissionbyid(id):
    return reddit.submission(id)

def mass_add():
    active_user_id = [u.id for u in User.query.filter(
        User.active == True, User.bot_id == 1, User.chat_id.isnot(None), User.subscriptions_active == True)]
    for u in active_user_id:
        try:
            for j in "suspiciouslyspecific, wellworn, wholesomememes, praisethecameraman, relationship_advice,mechanical_gifs, askreddit, dadjokes, jokes, coolguides, todayilearned".split(','):
                if len(j.strip()) > 0:
                    UserSubscription.create_subscription(u,j.strip())
        except Exception as e:
            log.debug(traceback.format_exc())    

def get_url_for_XKCD(comic_number):
    return f"https://xkcd.com/{comic_number}/info.0.json"

@celery.task
def update_XKCD(history_count=15):
    for i in range(1, history_count + 1):
        props = {}
        ci = ContentItem()
        ci.contentprovider_id = 2 #yea magic number i know
        url = get_url_for_XKCD(i)                
        try:
            response = requests.get(url)
            response.raise_for_status()
            payload = response.json()
            tags_to_add = ["xkcd.com"]            
            ci.title = payload['safe_title']
            ci.content_hash = get_md5(payload['num'])            
            ci.content_tags = [ContentTag.find_or_create_tag(tg) for tg in tags_to_add]
            ci.data = json.dumps(payload)
            ci.save_to_db()            
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            print(f'Other error occurred: {err}')  # Python 3.6           
 
from app.providers.reddit import RedditContentItemCreator
@celery.task
def update_reddit(subname, limit=1000):
    rcic = RedditContentItemCreator()    
    rcic.GetContent(subname=subname, limit=limit)    

@celery.task
def send_channel_content():
    send_content(2) #the bot will send to users of type 2 (channels)

@celery.task
def send_content(user_type=0):
    active_chat_ids = [u.chat_id for u in User.query.filter(
        User.active == True, User.subscriptions_active == True, User.user_type == user_type)]
    for u in active_chat_ids:
        try:
            send_random_quote(u)
        except telegram.error.Unauthorized as e:
            user = User.find_by_chatid(u)
            user.is_active = False
            user.subscriptions_active = False
            user.note = "{} - {}".format(user.note, "Unauthorized error")
            user.save_to_db()  
            send_system_message(distractobot, "A user bailed on us!",traceback.format_exc(),True, True)          
        except Exception as e:
            log.debug(traceback.format_exc())
            send_system_message(distractobot, "Exception during send_content!",traceback.format_exc(),False, False)          


@celery.task
def send_system_broadcast(chat_id):
    if random.random() < 0.006:  # once every 158 scheduled posts / #number of users
        n = Notification.get_latest()
        if n:
            distractobot.send_message(chat_id=chat_id, text="*{}* \n{}".format(n.title, n.text),parse_mode=telegram.ParseMode.MARKDOWN, disable_notification=True, disable_web_page_preview=True )
            return True
    return False

def get_random_user_tag(chat_id = None):    
    if not chat_id:
        chat_id = app.config['ADMIN_CHAT_ID']
    user = User.find_by_chatid(chat_id)       
    subs = UserSubscription.get_by_user(user.id) #can refactor to send only 1        
    return random.choice([t.keyvalue_entry.value for t in subs])

def get_button_data(content_id, quantifier, chat_id):
    d = json.dumps({                
        'q':quantifier,
        'c':chat_id,
        'i':content_id
    })    
    return d

def get_voting_keyboard(content_id, chat_id):
    seenoevil = emojize(":see_no_evil:", use_aliases = True)        
    down = emojize(":thumbsdown:", use_aliases = True)   
    up = emojize(":thumbsup:", use_aliases = True)    
    k = InlineKeyboardMarkup([[\
        InlineKeyboardButton(seenoevil,callback_data=get_button_data(content_id, 0, chat_id)),\
        InlineKeyboardButton(down,callback_data=get_button_data(content_id, 1, chat_id)),\
        InlineKeyboardButton(up,callback_data=get_button_data(content_id, 2, chat_id)),]])
    return k

@celery.task
def send_random_quote(chat_id=None, tag=None):
    if not chat_id:
        chat_id = app.config['ADMIN_CHAT_ID']
    user = User.find_by_chatid(chat_id)
    if user is None:
        return "User not found."
    if send_system_broadcast(chat_id):
        return "system message broadcast!"    
    # get user subscriptions
    quote = None
    
    if tag is not None:
        quote = ContentItem.return_random_by_tags([tag])

    if quote is None:
        tag = get_random_user_tag(user.chat_id)        
        quote = ContentItem.return_random_by_tags([tag])  #maybe the topic isn't populated so pick another
    
    if quote is None and user is not None:
        distractobot.send_message(chat_id=chat_id, text="You have no subscriptions. Are you registered?")
        send_system_message(distractobot, "User has no subscriptions. User will be disabled. {}".format(user.id))
        user.subscriptions_active = False
        user.save_to_db()
        return "No subscriptions found for user."    
    if ContentItemStat.does_statistic_exist(user, quote):
        return send_random_quote(chat_id, tag)

    payload = None
    payload = json.loads(quote.data)
    shortlink = payload.get('shortlink')
    url = payload.get('url', '')
    quote_id = quote.id      
    k = get_voting_keyboard(quote_id, chat_id)
    if ("nsfw" in quote.title.lower() or payload.get('over_18', False)) and not user.over_18_allowed:  # not allowed
        send_random_quote(chat_id, tag)
        return shortlink
    if len(payload.get('text', "").strip()) == 0:  # handle title only
        if not payload.get('is_photo', True) and not payload.get('is_video', True):            
            # no body so likely something like TIL or showerthoughts
            distractobot.send_message(
                chat_id, "{} \n{} ({})".format(quote.title, shortlink, tag), disable_web_page_preview=True, reply_markup = k, disable_notification=True)
            ContentItemStat.add_statistic(user, quote)
            return shortlink
        if payload.get('is_photo', False) or is_image(url):  # is photo            
            distractobot.send_photo(chat_id, payload.get(
                'url'), caption="{} - {} ({})".format(quote.title, shortlink, tag), reply_markup = k, disable_notification=True)
            ContentItemStat.add_statistic(user, quote)
            return shortlink
        if payload.get('is_video', False):  # is animation            
            distractobot.send_animation(chat_id, payload.get(
                'url'), caption="{} - {} ({})".format(quote.title, shortlink, tag), reply_markup = k, disable_notification=True)
            ContentItemStat.add_statistic(user, quote)
            return shortlink
        # no phot, no video let's see if it has a url
        if payload.get('url', False) and 'reddit.com/r/' not in payload.get('url'):            
            url = payload.get('url')
            if not url.startswith('https://v.redd.it'):                
                msg = "{} \nLearn more: [{}]({}) \n\nsource: [{}]({})".format(
                    quote.title, (url[:20] + '...') if len(url) > 21 else url, url,tag, shortlink)                
                distractobot.send_message(
                    chat_id, msg, parse_mode=telegram.ParseMode.MARKDOWN, disable_web_page_preview=True, reply_markup = k, disable_notification=True)
                ContentItemStat.add_statistic(user, quote)
                return shortlink
            if is_image(url):                
                distractobot.send_photo(
                    chat_id, url, caption="{} - {} ({})".format(quote.title, shortlink, tag), disable_notification=True)
                ContentItemStat.add_statistic(user, quote)
                return shortlink

        # we have no body and no pictures/videos , something like AskReddit so the comments are important
        if payload.get('comments', False):              
            comments = payload.get('comments')
            t = []
            for value in comments:
                t.append("\n" + emoji.emojize(":bust_in_silhouette:") +
                         " {} - {}".format(value, comments[value]))
            msg = "========================\n*{}* \n======================== \n{} \n[{}]({})".format(
                quote.title, "\n".join(t), tag, payload.get('original_url', 'https://reddit.com'), tag)
            distractobot.send_message(
                chat_id, msg, disable_web_page_preview=True, parse_mode=telegram.ParseMode.MARKDOWN, reply_markup = k, disable_notification=True)
            ContentItemStat.add_statistic(user, quote)
            return shortlink
            # build comment block
        send_system_message(distractobot, "Could not identify item. {}".format(shortlink))
        send_random_quote(chat_id, tag) #could not identify item
    else:
        # we have title + body saved
        title = quote.title
        text = payload.get('text', None)
        msg = "========================\n*{}* \n======================== \n{} \n[{}]({})".format(
            title, text, tag, shortlink)
        distractobot.send_message(
            chat_id, msg, parse_mode=telegram.ParseMode.MARKDOWN, disable_web_page_preview=True, reply_markup = k, disable_notification=True)
        ContentItemStat.add_statistic(user, quote)
        return shortlink

###############################################################################

    
