#!/usr/bin/env python

from telegram.ext import Updater, PrefixHandler, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
import telegram

from app import app, log, yebogrambot

from functools import wraps
import traceback

from emoji import emojize
from app.commontasks import send_system_message, role_required, error_callback, get_chat_id, send_typing_action


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
        context.bot.send_message(chat_id=chat_id, text="detected a swear word!")
        context.bot.delete_message(update.message.chat.id, update.message.message_id)
    else:
        update.message.reply_text(update.message.text)
    pass

#################################################################################   

def main():
    updater = Updater(app.config['YEBOGRAMBOT_API_KEY'], use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))    
    dp.add_handler(PrefixHandler(['!','#'],'cut', handle_censor))    
    dp.add_error_handler(error_callback)    
    updater.start_polling()
    log.info('Polling started')
    updater.idle()

if __name__ == '__main__':
    main()
