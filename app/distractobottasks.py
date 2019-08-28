from __future__ import unicode_literals
import json
import os
import requests
import emoji
import datetime
from app import app, make_celery, log, distracto_bot, mail
from app.main.models import ContentStats, UserSubscription, ContentItem, ContentTag, KeyValueEntry, Notification, ContentItemStat
from app.auth.models import User
from app.tasks import send_email
import time
import random
import datetime
import re
import traceback
from app.rbot import reddit
from app.utils import get_md5
from app import log, db
import telegram
from MySQLdb._exceptions import IntegrityError
from sqlalchemy.exc import InvalidRequestError

celery = make_celery(app)


def getsubmissionbyid(id):
    return reddit.submission(id)


def run_full_update():
    keys = KeyValueEntry.query.all()
    for key in keys:
        send_email("mailbox@a20.co.za", "{} started ".format(
            key.value), "nothing to see", deletable=True)
        update_reddit(key.value, 300)
        send_email("mailbox@a20.co.za", "{} completed ".format(
            key.value), "nothing to see", deletable=True)

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

@celery.task
def update_reddit(subname, limit=1000):
    props = {}
    srs = reddit.subreddit(subname).hot(limit=limit)
    j = 0
    for item in srs:
        j = j+1
        if item.stickied or item.pinned:
            continue
        ci = ContentItem()
        tags_to_add = [subname]
        props['id'] = item.id
        url = getattr(item, 'url', None)
        props['original_url'] = url
        ci.title = item.title
        props['text'] = getattr(item, 'selftext', None)
        if url or not 'https://www.reddit.com/r/' in url or not 'wikipedia' in url:
            if getattr(item, 'media', False):
                if 'reddit_video' in item.media:
                    url = item.media['reddit_video']['fallback_url']
                    props["is_video"] = True  # can send as gif
                if 'oembed' in item.media:
                    props['oembed'] = item.media['oembed']
                    if 'thumbnail_url' in item.media['oembed']:
                        url = item.media['oembed']['thumbnail_url']
                    if 'type' in item.media['oembed'] and item.media['oembed']['type'] == 'youtube.com':
                        ci.title = "{} - {}".format(
                            ci.title, item.media['oembed']['title'])
            # if photo only then s.preview[enabled] = True
            if hasattr(item, 'preview'):
                if 'reddit_video_preview' in item.preview:
                    if 'fallback_url' in item.preview['reddit_video_preview']:
                        url = item.preview['reddit_video_preview']['fallback_url']
                        props["is_video"] = True  # can send as gif
                if 'reddit_video' in item.preview:
                    if 'fallback_url' in item.preview['reddit_video']:
                        url = item.preview['reddit_video']['fallback_url']
                        props["is_video"] = True  # can send as gif

        props['url'] = url
        if is_image(url):
            props['is_photo'] = True
        if item.over_18:
            tags_to_add.append('_over_18')
            props["over_18"] = True
        if item.gilded:
            tags_to_add.append('_gilded')
            props["gilded"] = True
        props['total_awards_received'] = item.total_awards_received
        # set tags
        ci.content_tags = [ContentTag.find_or_create_tag(
            tg) for tg in tags_to_add]
        props['id'] = item.id
        props['shortlink'] = item.shortlink
        props['ups'] = item.ups
        props['downs'] = item.downs
        # we'll also save the top 5 top-level comments
        comments = {}
        ci.comment_sort = 'best'
        for i in range(5):
            if len(item.comments) > i:
                comments[i] = item.comments[i].body
        props['comments'] = comments
        ci.content_hash = get_md5(item.shortlink)
        ci.data = json.dumps(props)
        try:
            ci.save_to_db()
            log.info(
                '{} Processed item with reddit id {} - {} - {}'.format(j, item.id, item.title, item.shortlink))
        except InvalidRequestError as e:
            log.error(e)
            db.session.session.rollback()
        except IntegrityError as e:
            db.session.rollback()
            pass


@celery.task
def send_content():
    active_chat_ids = [u.chat_id for u in User.query.filter(
        User.active == True, User.subscriptions_active == True)]
    for u in active_chat_ids:
        try:
            send_random_quote(u)
        except telegram.error.Unauthorized as e:
            user = User.find_by_chatid(u)
            user.is_active = False
            user.subscriptions_active = False
            user.note = "{} - {}".format(user.note, "Unauthorized error")
            user.save_to_db()  
            send_system_message("A user bailed on us!",traceback.format_exc(),True, True)          
        except Exception as e:
            log.debug(traceback.format_exc())
            send_system_message("Exception during send_content!",traceback.format_exc(),True, True)          


@celery.task
def send_email(to, subject, plaintextMessage, deletable=True):
    subject = "{} {}".format(subject, " <deletable>") if deletable else subject
    try:
        receiver_email = to
        message = "Subject: {} \n\n {}".format(subject, plaintextMessage)
        msg = mail.send_message(subject, body=plaintextMessage,
                                sender=app.config['MAIL_DEFAULT_SENDER'], recipients=to.split(','))
        log.debug("Email with subject '{}' sent to {}.".format(subject, to))
    except Exception as e:
        log.debug(e)


@celery.task
def send_system_broadcast(chat_id):
    if random.random() < 0.006:  # once every 158 scheduled posts
        n = Notification.query.first()
        if n:
            distracto_bot.send_message(chat_id=chat_id, message="*{}* \n{}".format(n.title, n.text))
            return True
    return False


def is_image(url):
    return url.endswith('.jpg') or url.endswith('.jpeg') or url.endswith('.png')


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
    if not tag:            
        subs = UserSubscription.get_by_user(user.id) #can refactor to send only 1
        tag = random.choice([t.keyvalue_entry.value for t in subs])
    quote = ContentItem.return_random_by_tags([tag])
    if quote is None and user is not None:
        distracto_bot.send_message(chat_id=chat_id, text="You have no subscriptions. Are you registered?")
        send_system_message("User has not subscriptions. User will be disabled. {}".format(user.id))
        user.subscriptions_active = False
        user.save_to_db()
        return "No subscriptions found for user."
    payload = None
    payload = json.loads(quote.data)
    shortlink = payload.get('shortlink')
    url = payload.get('url', '')
    log.info(quote.data)
    if payload.get('over_18', False) and not user.over_18_allowed:  # not allowed
        send_random_quote(chat_id)
        return shortlink
    if len(payload.get('text', "").strip()) == 0:  # handle title only
        if not payload.get('is_photo', True) and not payload.get('is_video', True):
            log.debug("condition 1")
            # no body so likely something like TIL or showerthoughts
            distracto_bot.send_message(
                chat_id, "{} \n{}".format(quote.title, shortlink), disable_web_page_preview=True)
            ContentItemStat.add_statistic(user, quote)
            return shortlink
        if payload.get('is_photo', False) or is_image(url):  # is photo
            log.debug("condition 2")
            distracto_bot.send_photo(chat_id, payload.get(
                'url'), caption="{} - {}".format(quote.title, shortlink))
            ContentItemStat.add_statistic(user, quote)
            return shortlink
        if payload.get('is_video', False):  # is animation
            log.debug("condition 3")
            distracto_bot.send_animation(chat_id, payload.get(
                'url'), caption="{} - {}".format(quote.title, shortlink))
            ContentItemStat.add_statistic(user, quote)
            return shortlink
        # no phot, no video let's see if it has a url
        if payload.get('url', False) and 'reddit.com/r/' not in payload.get('url'):
            log.debug("condition 4")
            url = payload.get('url')
            if not url.startswith('https://v.redd.it'):
                log.debug("condition 4.1")
                msg = "{} \nLearn more: [{}]({}) \n\nsource: [{}]({})".format(
                    quote.title, (url[:20] + '...') if len(url) > 21 else url, url, tag, shortlink)
                log.debug(msg)
                distracto_bot.send_message(
                    chat_id, msg, parse_mode=telegram.ParseMode.MARKDOWN, disable_web_page_preview=True)
                ContentItemStat.add_statistic(user, quote)
                return shortlink
            if is_image(url):
                log.debug("condition 4.2")
                distracto_bot.send_photo(
                    chat_id, url, caption="{} - {}".format(quote.title, shortlink))
                ContentItemStat.add_statistic(user, quote)
                return shortlink

        # we have no body and no pictures/videos , something like AskReddit so the comments are important
        if payload.get('comments', False):
            log.debug("condition 5")            
            comments = payload.get('comments')
            t = []
            for value in comments:
                t.append(emoji.emojize("\n:thought_balloon:") +
                         " {} - {}".format(value, comments[value]))
            msg = "========================\n*{}* \n======================== \n{} \n[{}]({})".format(
                quote.title, "\n".join(t), tag, payload.get('original_url', 'https://reddit.com'))
            distracto_bot.send_message(
                chat_id, msg, disable_web_page_preview=True, parse_mode=telegram.ParseMode.MARKDOWN)
            ContentItemStat.add_statistic(user, quote)
            return shortlink
            # build comment block
        send_random_quote(chat_id)
    else:
        # we have title + body saved
        title = quote.title
        text = payload.get('text', None)
        msg = "========================\n*{}* \n======================== \n{} \n[{}]({})".format(
            title, text, tag, shortlink)
        distracto_bot.send_message(
            chat_id, msg, parse_mode=telegram.ParseMode.MARKDOWN, disable_web_page_preview=True)
        ContentItemStat.add_statistic(user, quote)
        return shortlink

###############################################################################

@celery.task
def send_bot_message(chat_id, messageText):
    distracto_bot.send_message(chat_id, messageText, disable_web_page_preview=True)

@celery.task
def send_system_message(subject, plainTextMessage=None, email=False, send_to_bot=True):
    if send_to_bot:
        send_bot_message(ADMIN_CHAT_ID, subject)
    if email:
        send_email.delay(TASK_NOTIFICATION_EMAIL, subject,
                         "Nothing here." if plainTextMessage is None else plainTextMessage, True)
    log.info("{} \t {}".format(subject, plainTextMessage))