#!/usr/bin/env python

from telegram.ext import Updater, PrefixHandler, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
import telegram
import colorama
import time
import random
from enum import Enum
from app import app, log, yebogrambot

from functools import wraps
import traceback

from emoji import emojize
from app.yebogram.common import contains_instagram_link,\
    get_media_code_from_url, get_likes_and_comments_by_media
from app.commontasks import send_system_message, role_required,\
    error_callback, get_chat_id, send_typing_action
     

channel_id = "-1001126850930"

channel_admins = []

class WorkItem:
    def __init__(self, url, expiryInSeconds=86400):
        self._url = url
        self._expiryInSeconds = expiryInSeconds
        self._createdEpoch = time.time()

    def isExpired(self):
        return self._createdEpoch + self._expiryInSeconds <= time.time()
    
    def __repr__(self):
        return self._url

    pass


class WorkItemManager:
    _workItems = []

    def __init__(self, workItemLimit=10):
        self._workItemLimit = workItemLimit

    def getWorkItems(self):        
        return self._workItems

    def addWorkItem(self, url):
        self._workItems.append(WorkItem(url))
    

    pass

#-------------------------------------------------------
workItemManager = WorkItemManager()
#-------------------------------------------------------
@send_typing_action
def start(update, context):
    """Start function. Displayed when the /start command is called.
    """
    message = "Ok, started."
    update.message.reply_text(message)


@send_typing_action
def handle_censor(update, context):
    t = update.message.text
    if ("vloek" in t):
        chat_id = get_chat_id(update)
        context.bot.send_message(
            chat_id=chat_id, text="detected a swear word!")
        context.bot.delete_message(
            update.message.chat.id, update.message.message_id)
    else:
        update.message.reply_text(update.message.text)
    pass


@send_typing_action
def relay_to_backoffice(update, context):
    msg = " ".join(context.args)
    u = update.message.from_user.id
    msg = f"Message from {update.message.from_user.first_name}: {msg}"
    yebogrambot.send_message(channel_id, msg, disable_web_page_preview=False)
@send_typing_action
def display_list(update,context):
    channel_id = update.message.chat.id
    
    yebogrambot.send_message(channel_id, msg, disable_web_page_preview=False)
    pass

def is_valid_channelid(chan_id):
    return chan_id in [-1001126850930]  # channels the bot is active on


def get_main_keyboard():
    ck = [['Name', 'Type'],
          ['Max Warns', 'Ban Types'],
          ['Welcome', 'Rules'],
          ['Drops Only', 'Same Account'],
          ['Delete Leecher Messages', 'UTM Ban'],
          ['Minimum Followers', 'Temporary Messages'],
          ['Premium Users', 'Auto Drops'],
          ['Remove Group'],
          ['Minimum Back']
          ]
    return telegram.ReplyKeyboardMarkup(ck)


def show_keyboard(update, context):
    channel_id = update.message.chat.id
    yebogrambot.send_message(
        channel_id, text="showing custom", reply_markup=get_main_keyboard())


def process_all(update, context):
    chan_id = update.message.chat.id
    # check that user is not an admin then restrict them from can_add_web_page_previews
    # yebogrambot.restrict_chat_member
    #restrict_chat_member(chat_id, user_id, until_date=None, can_send_messages=None, can_send_media_messages=None, can_send_other_messages=None, can_add_web_page_previews=None, timeout=None, **kwargs)
    if is_valid_channelid(chan_id):
        if contains_instagram_link(update.message.text):
            log.info(emojize(
                f":exclamation: I see an instagram link :exclamation: from :point_right:  {update.message.from_user.id}", True))
            send_message(channel_id, "Please do some work. @{}".format(
                update.message.from_user.username))
    pass


def send_message(chan_id, message, disable_web_page_preview=True):
    yebogrambot.send_message(
        chan_id, message, disable_web_page_preview=disable_web_page_preview)

#################################################################################


def main():
    colorama.init()
    updater = Updater(app.config['YEBOGRAMBOT_API_KEY'], use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('showkeyboard', show_keyboard))
    dp.add_handler(CommandHandler('ask', relay_to_backoffice))
    dp.add_handler(CommandHandler('list', display_list))
    # leave as fall through
    dp.add_handler(MessageHandler(Filters.text, process_all))
    dp.add_error_handler(error_callback)
    updater.start_polling()
    log.info('Polling started')
    updater.idle()


if __name__ == '__main__':
    print("%" * 20)
    items = ["https://www.instagram.com/p/B2Uhl8qArdM/"]    
    items.append("https://www.instagram.com/p/B2UmD6hn3rt/")
    items.append("https://www.instagram.com/p/B2P3oAfnRSf/")
    items.append("https://www.instagram.com/p/B2PDegwHchw/")
    items.append("https://www.instagram.com/p/B2E2mXkHfuK/")

    for item in items:
        workItemManager.addWorkItem(item)
    
    for item in workItemManager.getWorkItems():
        sc = get_media_code_from_url(str(item))
        data = get_likes_and_comments_by_media(sc,2)
        for k in data.keys():
            likes = data['likes']
            comments = data['comments']
            print(f"==============================================-- {sc}")
            for like in likes:                
                #print(f"\t\tliked (by) {like}")
                pass
            print("--")
            for comment in comments:
                print(dir(comment))
                pass
                #print(comment.identifier)                        
                #print(f"\t\t{comment.text} (by) @{comment}")                        
        print("-----------------------------")
    #main()
