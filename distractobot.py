#!/usr/bin/env python
from telegram.ext import Updater, CommandHandler, MessageHandler, RegexHandler
from telegram.ext import ConversationHandler, CallbackQueryHandler, Filters, InlineQueryHandler,ChosenInlineResultHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatAction
from telegram import  InlineQueryResultArticle, ParseMode, InputTextMessageContent
import telegram
import requests
import re
import datetime
import json
from colorama import Fore, Back, Style

from app import app, log, redis_instance, distractobot
from app.auth.models import User, Role
from app.main.models import UserSubscription, ContentStats, Bot_Quote, KeyValueEntry, ContentItemStat,ContentItemInteraction
from app.utils import generate_random_confirmation_code

import traceback
import random
from uuid import uuid4
from emoji import emojize
from app.commontasks import send_system_message, role_required, send_typing_action, error_callback, get_chat_id
from app.distractobottasks import send_random_quote, update_reddit #send_random_quote has a dep on bot

EMAIL_REGEX = "^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$"

GET_EMAIL_ANSWER, GET_EMAIL, ACTIVATE = range(3)

email = None

@send_typing_action
def start(update, context):
    """Start function. Displayed when the /start command is called.
    """
    keyboard = [['Send Now', '/register']]
    message = "Hello, I'm DistractoBot. I'll send you something interesting every hour. Enter /cancel to cancel this conversation at any time."
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(message, reply_markup=reply_markup)

@send_typing_action
def send_now(update, context): #-1001331321081
    chat_id = get_chat_id(update)
    if user_exists(chat_id=chat_id):
        log.info('Sending /sendnow to {}'.format(chat_id))
        send_random_quote(chat_id)
    else:
        message = emojize("You need to register for that. Send /register :lock:", use_aliases=True)
        update.message.reply_text(message)
    return

@send_typing_action
def start_registration(update, context):
    chat_id = get_chat_id(update)
    if user_exists(chat_id=chat_id):        
        return activate(update, context)
    
    keyboard = [['Yes', 'No']]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True)
    message = "Would you like to sign up for announcements?"
    update.message.reply_text(message,  reply_markup=reply_markup)
    return GET_EMAIL_ANSWER

@send_typing_action
def get_email_answer(update, context):
    chat_id = get_chat_id(update)
    process_and_save_response(chat_id, "email_answer", update.message.text)
    if update.message.text == "No":
        return skip_get_email(update, context)
    message = "Ok, please enter your email address now. Enter /skip if you change your mind."
    update.message.reply_text(message)
    return GET_EMAIL

@send_typing_action
def get_email(update, context):
    chat_id = get_chat_id(update)
    email = update.message.text
    process_and_save_response(chat_id, "email_value", email)
    update.message.reply_text("Ok, you entered {} ".format(email))
    return activate(update, context)

@send_typing_action
def skip_get_email(update, context):    
    chat_id = get_chat_id(update)
    process_and_save_response(chat_id, "email_value", "{}@none".format(chat_id))    
    return activate(update, context)

@send_typing_action
def activate(update, context):
    chat_id = get_chat_id(update)            
    user = User.find_by_chatid(chat_id)    
    if not user is None:
        if not user.active:
            update.message.reply_text("Sorry, there seems to be a problem with your account. An administrator has been notified.", reply_markup=ReplyKeyboardRemove())    
            return
        if not user.subscriptions_active:        
            user.subscriptions_active = True
            user.save_to_db()
            update.message.reply_text(emojize("Ok, your account has been activated. :white_check_mark: ", use_aliases=True), reply_markup=ReplyKeyboardRemove())        
        else:
            return view_status(update, context)
    else:   
        password = generate_random_confirmation_code(10)
        create_activated_user(chat_id, context, email="{}@{}".format(chat_id,"none"))
    return ConversationHandler.END

@send_typing_action
def cancel(update, context):
    """
    Use cancellation function.
    """
    user = update.message.from_user
    update.message.reply_text("Ok, bye.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

@send_typing_action
def unsubscribe(update, context):
    user = User.find_by_chatid(get_chat_id(update))
    user.subscriptions_active = False
    user.save_to_db()
    update.message.reply_text(emojize("Ok, you've been unsubscribed. If you change your mind just send /activate", use_aliases=True))

@send_typing_action
def viewsubscriptions(update, context):
    user = User.find_by_chatid(get_chat_id(update))
    chat_id = get_chat_id(update)    
    if user is None:
        distractobot.send_message(chat_id=chat_id,text="You are not registered.")
        return    
    subs = UserSubscription.get_by_user(user.id)
    rep = "Your subscribed topics are: \n" + "\n".join(["https://www.reddit.com/r/{}".format(s.keyvalue_entry.value) for s in subs])
    update.message.reply_text("Ok, {}".format(rep), disable_web_page_preview=True)

@send_typing_action
def terminate(update, context):
    user = User.find_by_chatid(get_chat_id(update))
    user.active = False
    user.note = "User terminated."
    user.save_to_db()
    update.message.reply_text("Ok, your account has been closed.")

@send_typing_action
def update_email(update, context):
    email = "".join(context.args)
    if not re.match(EMAIL_REGEX, email):
        update.message.reply_text(emojize("Oops, that does not look like a valid email address. Try again? Send /updateemail", use_aliases=True))
    else:
        if User.find_by_email(email) is not None:
            update.message.reply_text("It looks like that email is used by someone else.")
        else:
            chat_id = get_chat_id(update)
            user = User.find_by_chatid(chat_id)
            if user is not None:
                user.email = email
                user.save_to_db()
                update.message.reply_text("Ok, your email address was updated to '{}'.".format(email))
            else:
                update.message.reply_text("You need to register first. Send /register")

@send_typing_action
def add_subscription(update, context):    
    update.message.reply_text(emojize("Not implemented yet but stay tuned! Sign up for email announcements? Send /updateemail"))

@role_required("admin")
@send_typing_action
def trigger_update(update, context):
    subreddit = context.args[0]    
    update_reddit.delay(subreddit)

@send_typing_action
def view_status(update, context):        
    if not user_exists(chat_id= get_chat_id(update)):
        update.message.reply_text(emojize("You are not registered. :lock:", use_aliases=True))
        return
    
    user = User.find_by_chatid(get_chat_id(update))
    if not user.active:
        update.message.reply_text(emojize("Your account is not active."))
        return
    if not user.subscriptions_active:
        update.message.reply_text(emojize("Your subscriptions have been suspended. To re-activate just send /activate", use_aliases=True))
        return
    update.message.reply_text(emojize("Your account is active and set to receive updates. :white_check_mark:", use_aliases=True))
        

@send_typing_action
def shift_time(update, context):
    user = User.find_by_chatid(get_chat_id(update))
    if user is None:
        update.message.reply_text("It looks like you're not registered.")
    else:
        try:
            o = int("".join(context.args))
            if o > 14 and o < -12:
                raise ValueError
            user.utc_offset = o
            user.save_to_db()
            update.message.reply_text("Ok, your time offset has been updated to UTC {}".format(user.utc_offset))
        except ValueError:            
            update.message.reply_text("Oops, enter a number in the form 2, -2 or +11 and between -12 and +14")  

@send_typing_action
def about(update, context):
    update.message.reply_text("This bot sends you one item of top-rated reddit content every hour. Use it to break out of a rut. Or watch this video I recommend! https://www.youtube.com/watch?v=XVbH_TkJW9s Need to contact its creator? Send /toadmin <your message here>", disable_web_page_preview=True)

@send_typing_action
def help(update, context):
    update.message.reply_text("Type @distractobot <subredditname> to get a list of available subs. \nBring up the menu of public commands by entering / on your keyboard.")

@send_typing_action
def cause_error(update, context):
    p = 1/0
    update.message.reply_text("Error handled!")
##############################################################################

def user_exists(**kwargs):
    return User.exists(**kwargs)

def create_activated_user(chat_id, context, email=None, note=None):        
    if User.exists(chat_id=chat_id):
        context.bot.send_message(chat_id=chat_id, text="It looks like you're already registered.")
        return
    usr = User.find_by_chatid(chat_id)    
    new_user = User(password=User.generate_hash("{}dp".format(chat_id)), chat_id=chat_id)
    new_user.chat_id = chat_id
    new_user.bot_id = 1
    new_user.email = email if email is not None else "{}@null".format(chat_id)
    new_user.subscriptions_active = True
    new_user.active = True
    new_user.note = note if not note is None else "Auto activated"
    new_user.user_type = 1
    new_user.save_to_db()
    # add random content    
    #default_subs = [str(x) for x in get_key("SYSTEM_CACHE", "default_subs").split(',')]
    #for content_id in default_subs:
    #    usb = UserSubscription()
    #    usb.user_id = new_user.id
    #    usb.content_id = int(content_id)
    #    usb.save_to_db()
    send_system_message(distractobot, "New account created! {} Email: '{}'".format(chat_id, new_user.email), True)
    context.bot.send_message(chat_id=chat_id, text="Ok, your account has been created and some default topics have been added. View them by sending /viewsubs If you want to view all available topics enter '@DistractoBot <search>'")
    context.bot.send_message(chat_id=chat_id, text="And, to suspend your subscription just send /unsubscribe")

@send_typing_action
@role_required("admin")
def get_content_stats(update, context):
    chat_id = get_chat_id(update)    
    stats = ContentItemStat.get_top_stats(10)
    msg = "=============== \n*TOP 10 CONTENT ITEMS* \n=============== \n"+ "\n".join(["{} - {} - {}".format(k, stats[k]['count'], stats[k]['last_updated']) for k in stats])
    context.bot.send_message(chat_id=chat_id, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)


def selectResult(update, context):
    query = update.chosen_inline_result    
    cid = query.to_dict()["from"]["id"]        
    context.bot.send_message(chat_id=cid, text="You selected {}".format(query.result_id))    
    send_random_quote.delay(cid, query.result_id)

@send_typing_action
def inlinequery(update, context):
    update.inline_query.answer("Tapper")
    #query = update.inline_query.query        
    #values = [value for value in get_key("SYSTEM_CACHE","reddits_list").split(",") if query in value]    
    #results = [InlineQueryResultArticle(
    #    id = v,
    #    title=v,
    #    input_message_content=InputTextMessageContent(v)) for v in values]  
    #update.inline_query.answer(results)

def register(update, context):
    chat_id = get_chat_id(update)    
    create_activated_user
    context.bot.send_message(chat_id=chat_id, text="Registration is closed for now. Catch the public channel at https://t.me/randomdistractions Same great content, but you get the chef's choice.")
    
################################################################################# 

@send_typing_action
def upvotes(update, context):
    keyboard = [[InlineKeyboardButton("Up",callback_data='up'),
    InlineKeyboardButton("Down", callback_data="down"), InlineKeyboardButton("Publish", callback_data="pub", switch_inline_query="publisher")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("choose",reply_markup=reply_markup)
    pass

def button(update,context):        
    query = update.callback_query       
    user_id = update.effective_user.id    
    user_name = update.effective_user.username
    message_id = update.callback_query.message.message_id        
    c = ContentItemInteraction.query.filter_by(message_id=message_id,user_id=user_id).first()
    already_voted=False
    vote_changed = True
    choice = 0
    contentitem_id = None
    if c is None: #unanswered                
        if ("{" in query.data): #first person to answer and answer first time answering
            data = json.loads(query.data)
            contentitem_id = data['i']
            choice = data['q']
        else:            
            contentitem_id = None #second+ person to answer
            choice = query.data
        ContentItemInteraction.add_interaction(choice=choice, contentitem_id=contentitem_id, user_id=user_id, user_name=user_name, data=query.data, message_id=message_id)                 
        pass
    else:       #previous answer found
        already_voted=True          
        old_choice = None
        new_choice = None
        data = ""
        if ("{" in c.data): 
            data = json.loads(c.data)            
            old_choice = data['q'] #the old answer         
            data['q'] = query.data
            data = json.dumps(data)            
        else:                        
            old_choice = c.data
            data = query.data                    
        vote_changed = old_choice != update.callback_query.data 
        c.delete()
        ContentItemInteraction.add_interaction(choice=update.callback_query.data, contentitem_id=c.contentitem_id, user_id=user_id, user_name=user_name, data=data, message_id=message_id)         
        
    stats = ContentItemInteraction.get_interaction_stats(message_id)        
    sno = 0
    dw = 0
    u = 0
    for i in stats:
        if i['choice']==0:
            sno = i['count']
        if i['choice']==1:
            dw = i['count']
        if i['choice']==2:
            u = i['count']    
    seenoevil = emojize(f":see_no_evil: {'+' if sno > 0 else ''}{sno}", use_aliases = True)        
    down = emojize(f":thumbsdown: {'-' if dw > 0 else ''}{dw}", use_aliases = True)   
    up = emojize(f":thumbsup: {'+' if u > 0 else ''}{u}", use_aliases = True)    
    
    k = InlineKeyboardMarkup([[\
        InlineKeyboardButton(seenoevil,callback_data=0),\
        InlineKeyboardButton(down,callback_data=1),\
        InlineKeyboardButton(up,callback_data=2),]])
    
    if vote_changed:
        query.edit_message_reply_markup(inline_message_id=update.callback_query.inline_message_id, reply_markup=k)
    
    if not already_voted:
        distractobot.answerCallbackQuery(query.id, text="Thanks for voting!")
    else:
        if vote_changed:
            distractobot.answerCallbackQuery(query.id, text="Your vote was updated!")
        else:
            distractobot.answerCallbackQuery(query.id, text="Ay karamba!")

@send_typing_action
def vote(update, context):
    up = emojize(":thumbsup:", use_aliases = True)    
    down = emojize(":thumbsdown:", use_aliases = True)   
    seenoevil = emojize(":see_no_evil:", use_aliases = True)    
    k = InlineKeyboardMarkup([[\
        InlineKeyboardButton(seenoevil,callback_data='closedeyes'),InlineKeyboardButton(down,callback_data='down'),InlineKeyboardButton(up,callback_data='up'),]])            
    distractobot.send_photo(chat_id=app.config['ADMIN_CHAT_ID'], photo="https://i.some-random-api.ml/zfU7Q5dabr.jpg", caption="xxx", reply_markup = k)
    
@send_typing_action
def send_admin(update, context):
    chat_id = get_chat_id(update)
    send_system_message(distractobot, " ".join(context.args) + " (from chatid: {})".format(chat_id), True)    

def send_system_message(bot = None, text = None, to_bot=True, also_email=False):
    if bot and to_bot:
        bot.send_message(chat_id=app.config['ADMIN_CHAT_ID'], text="MESSAGE TO ADMIN: {} ".format(text))
    if also_email:
        bot.delay(app.config['NOTIFICATIONS_RECIPIENT_EMAIL'], "Message to admin", text, deletable=True)
    return


def process_and_save_response(redis_key, key, value):
    log.debug("logging to redis: key: '{}' value:'{}'".format(key,value))
    if not redis_instance.exists(redis_key):
        redis_instance.hmset(redis_key, {'__start__': datetime.datetime.now().strftime('%c')})
    log.debug('getting data')
    data = redis_instance.hgetall(redis_key)
    data[key] = value
    data['__lastupdate__'] = datetime.datetime.now().strftime('%c')
    log.debug('setting data')
    redis_instance.hmset(redis_key, data)
    log.debug("data saved")


def get_key(redis_key, key):
    print(redis_key + ":" + key)
    r = redis_instance.hget(redis_key, key).decode('utf-8')    
    return r


def main():
    updater = Updater(app.config['DISTRACTOBOT_API_KEY'], use_context=True)

    dp = updater.dispatcher    

    dp.add_handler(CommandHandler('start', start))

    dp.add_handler(MessageHandler(Filters.regex('^Send Now$'), send_now))
    dp.add_handler(CommandHandler('upvotes', upvotes))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(CommandHandler('toadmin', send_admin))
    dp.add_handler(CommandHandler('contentstats', get_content_stats))
    dp.add_handler(CommandHandler('sendnow', send_now))
    dp.add_handler(CommandHandler('suspend', unsubscribe))
    dp.add_handler(CommandHandler('viewsubs', viewsubscriptions))        
    dp.add_handler(CommandHandler('updateemail', update_email))
    dp.add_handler(CommandHandler('shifttime', shift_time))
    dp.add_handler(CommandHandler('status', view_status))
    dp.add_handler(CommandHandler('activate', activate))
    dp.add_handler(CommandHandler('error', cause_error))
    dp.add_handler(CommandHandler('addsub', add_subscription))
    dp.add_handler(CommandHandler('updatesub',trigger_update))
    dp.add_handler(CommandHandler('about', about))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('register', register))
    dp.add_handler(CommandHandler('vote', vote))
    dp.add_handler(InlineQueryHandler(inlinequery))

    dp.add_handler(ChosenInlineResultHandler(selectResult))


    registrationConversation = ConversationHandler(
        entry_points=[CommandHandler('register786', start_registration)],
        states={
            GET_EMAIL_ANSWER: [RegexHandler('Yes|No', get_email_answer)],
            GET_EMAIL: [RegexHandler(EMAIL_REGEX, get_email),
                        CommandHandler('skip', skip_get_email)],
            ACTIVATE: [MessageHandler(Filters.text, activate)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(registrationConversation)

    dp.add_error_handler(error_callback)
    # set redis cache
    # get_key("SYSTEM_FLASH","default_subs").split(',')
    process_and_save_response("SYSTEM_CACHE", "default_subs", "179,175,167,137,177,155,213,178,173,181,193,166")
    values = KeyValueEntry.query.all()   #read this from redis
    values = [v.value for v in values]    
    process_and_save_response("SYSTEM_CACHE","reddits_list", ",".join(values))
    updater.start_polling()
    log.info('Polling started')
    updater.idle()


if __name__ == '__main__':
    main()
