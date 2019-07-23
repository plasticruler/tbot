import datetime
import json
import os
import random
import re
import uuid
from urllib import parse
from flask import request

import redis
import telebot
import re

from app import app, bot, log

from app.main.models import Bot_Quote, SelfLog, EquityInstrument
from app.auth.models import User
from app.utils import generate_random_confirmation_code

from app.tasks import download_youtube, send_system_notification, save_inbound_message, send_email, send_random_quote, send_chart

redis_instance = redis.Redis(host=app.config['REDIS_SERVER'], port=app.config['REDIS_PORT'],
                             password=app.config['REDIS_PASSWORD'], charset='utf-8', decode_responses=True)

authorised_usernames = app.config['FAMILY_GROUP'].split(',')
#set up hook
@app.route('/{}'.format(app.config['BOT_SECRET']), methods=['POST', 'GET'])
def webhook():            
    if request.method == 'POST':
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)            
            bot.process_new_updates([update])
            return ''
        else:
            flask.abort(403)
            return 'Ok'
    else:
        return 'Ko'

# BOT RELATED
@bot.message_handler(commands=['help', 'domath','start', 'convert', 'quote', '8ball', 'register', 'slog','chart','activate','addsub'])
def send_welcome(message):
    save_inbound_message.delay(str(message))
    chat_id = message.chat.id    
    if "/quote" in message.text and message.chat.type == "private":
        send_random_quote(chat_id)
    elif '/addsub' in message.text and message.chat.type == "private":
        usr = User.find_by_chatid(chat_id)
        if usr is not None:
            pass
        else:
            bot.reply_to(message,"You're not registered.")
    elif "/chart" in message.text and message.chat.type == "private":
        codes = message.text.split()
        code = 'STXNDQ'
        if len(codes) >= 2:
            code = codes[1]
        send_chart(code, chat_id)
    elif "/domath" in message.text and message.chat.type == "private":
        bot.reply_to(message, "What's the op? add or multiply?")
        bot.register_next_step_handler_by_chat_id(chat_id, process_operator)
    elif "/register" in message.text and message.chat.type == "private":
        msg = bot.reply_to(message, "Ok {}, what is your email address?".format(message.from_user.first_name))
        bot.register_next_step_handler(msg, process_email_step)
        log.debug('nextstep registered')
        redis_key = "{}-register".format(chat_id)
        process_and_save_response(redis_key, "firstname", message.from_user.first_name)        
        log.debug('data logged to redis')
    elif "/activate" in message.text and message.chat.type == "private":
        activate_account(message)
    elif "/slog" in message.text and message.chat.type == "private":
        if message.chat.type == "private":
            sl = SelfLog()
            sl.chat_id = chat_id
            sl.message = message.text
            sl.save_to_db()
            bot.reply_to(message, 'Ok, message logged')
    elif "/convert" in message.text:
        if not message.chat.type == "private":
            bot.send_message(message.chat.id, "{} sorry, you need to send that command in a private chat.".format(
                message.from_user.first_name))
            return
        if message.chat.username not in authorised_usernames:
            bot.send_message(message.chat.id, "{} sorry, but you are not authorised to use this command.".format(
                message.from_user.first_name))
            return
        if message_contains_youtube_url(message):
            handle_convert_command(message)
    else:
        bot.send_message(message.chat.id, 'Ok {}. Go ahead.'.format(
            message.from_user.first_name))
def process_operator(message):
    chat_id = message.chat.id
    redis_key = "{}-math".format(chat_id)
    process_and_save_response(redis_key,"operator",message.text)
    bot.send_message(chat_id, "Ok, what number must I do the operator to 4590?")
    bot.register_next_step_handler_by_chat_id(chat_id, )
    pass
def process_answer(message):
    chat_id = message.chat.id
    redis_key = "{}-math".format(chat_id)
    process_and_save_response(redis_key,"number", message.text)
    n = get_key(redis_key,"number")
    op = get_key(redis_key,"operator")
    result = 0
    if op=="add":
        result = 4590 + int(n)
    if op == "multiply":
        result = 4590 * int(n)
    bot.send_message(chat_id,"Answer is: {}", result)
    pass
def addsub(message):
    chat_id = message.chat.id
    user = User.find_by_chatid(chat_id)
    if user is None:
        bot.send_message(chat_id, "It doesn't look like you've registered. Try /register and follow the prompts.")
        return

def process_email_step(message):
    try:
        chat_id = message.chat.id
        email = message.text
        redis_key = "{}-register".format(chat_id)
        process_and_save_response(redis_key, "email", email)
        data = redis_instance.hgetall(redis_key)                
        user = User.find_by_email(email)
        if user is not None:
            bot.send_message(chat_id, 'It looks like {} has already registered.'.format(email))
            return
        bot.send_message(chat_id, "Ok {}, I'll send a message to {} containing your confirmation code. Enter '/activate <activation_code>' here when you receive it.".format(get_key(redis_key, 'firstname'),
                                                                                        get_key(redis_key, 'email')))
        password = generate_random_confirmation_code(10)
        new_user = User(email=email, password=User.generate_hash(password), chat_id = chat_id)        
        new_user.save_to_db()
        send_email.delay(email,"@GennieTheBot activation code", "Your activation code is {}. In a private message to the bot, please enter '/activate {}' to activate your account. Your password is {}. If this email was sent in error please ignore it.".format(new_user.confirmation_code,new_user.confirmation_code, password))
    except Exception as e:        
        send_system_notification("[tbot] exception",str(e),email=True,send_to_bot=true)
        

    
def activate_account(message):
    chat_id = message.chat.id
    user = User.find_by_chatid(chat_id)
    if user is None:
        bot.send_message(chat_id, "It doesn't look like you've registered. Try /register and follow the prompts.")
        return
    registration_code = message.text.split()[1] if len(message.text.split()) == 2 else "none"
    if registration_code == "none":
        bot.send_message(chat_id, "Sorry, that command is invalid. Try /activate <activation_code>")
        return
    if user.confirmation_code == registration_code:
        user.email_confirmed_at = datetime.datetime.now()
        user.active = True
        user.subscriptions_active = True
        user.save_to_db()
        bot.send_message(chat_id, "Great, your account is activated! An email was sent to {}.".format(user.email))
        send_email(user.email, "@DistractoBot account details","Hi, Your account is available at {}. Your username is {}, and your password was sent to you previously. \n \nHave fun".format("https://zjremote.duckdns.org/bot/profile", user.email))
    else:
        bot.send_message(chat_id, "Looks like you've entered an invalid active code.")


def message_contains_youtube_url(message):
    youtubes = re.findall(
        r"(https?://(www|m).youtube.(com|be)/watch\?v=\S{11})", message.text)
    youtube_id = None
    if len(youtubes) > 0:
        url = youtubes[0][0]
        youtube_id = dict(parse.parse_qs(parse.urlsplit(url).query))['v'][0]

    if len(youtubes) == 0:  # try a different way
        youtubes = re.findall(
            r"(https?://youtu.(be|com)/\S{11})", message.text)
        if len(youtubes) > 0:
            youtube_id = youtubes[0][0].split('/')[1]

    return len(youtubes) > 0


def handle_convert_command(message):
    youtubes = re.findall(
        r"(https?://(www|m).youtube.(com|be)/watch\?v=\S{11})", message.text)
    youtube_id = None
    if len(youtubes) > 0:
        url = youtubes[0][0]
        youtube_id = dict(parse.parse_qs(parse.urlsplit(url).query))['v'][0]

    if len(youtubes) == 0:  # try a different way
        youtubes = re.findall(
            r"(https?://youtu.(be|com)/\S{11})", message.text)
        youtube_id = youtubes[0][0].split('/')[1]

    if len(youtubes) > 0:
        yurl = youtubes[0][0]
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Yes', 'No')
        msg = bot.reply_to(
            message, "Do you want me to download and convert this video to mp3?", reply_markup=markup)
        # save to redis
        bot.send_message(ADMIN_CHAT_ID, "User {} is trying to convert youtube file {}".format(
            message.from_user.username, yurl))
        save_args_to_redis("{}-youtube-download".format(message.chat.id), youtube_url=yurl, youtube_id=youtube_id, chat_id=message.chat.id,
                           stamp=datetime.datetime.now().strftime('%s'), email=ADMIN_EMAIL, username=message.from_user.username)
        bot.register_next_step_handler(msg, confirm_youtube_download)
    else:
        bot.send_message(
            "Sorry, but I don't understand your command. Try this /convert <youtube_url>")


def confirm_youtube_download(message):
    if message.text == 'Yes':
        # retrieve args from redis
        args = json.loads(redis_instance.get(
            "{}-youtube-download".format(message.chat.id)))
        download_youtube.delay(
            message.chat.id, args['youtube_url'], json.dumps(args))
        pass
    else:
        bot.reply_to(message, 'Ok')
########################



def process_age_step(message):
    try:
        chat_id = message.chat.id
        age = message.text
        if not age.isdigit():
            msg = bot.reply_to(message, 'Age should be a number.')
            bot.register_next_step_handler(msg, process_age_step)
            return
        redis_key = "{}-register".format(chat_id)
        process_and_save_response(redis_key, "age", age)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Male', 'Female')
        msg = bot.reply_to(message, "What is your gender?",
                           reply_markup=markup)
        bot.register_next_step_handler(msg, process_gender_step)
    except Exception as e:
        log.error(str(e))
        send_system_notification("[tbot] exception",str(e),email=True,send_to_bot=true)


def process_gender_step(message):
    chat_id = message.chat.id
    gender = message.text
    if gender not in ('Male', 'Female'):
        msg = bot.reply_to(message, 'Gender should be either Male or Female')
        bot.register_next_step_handler(msg, process_gender_step)
        return
    redis_key = "{}-register".format(chat_id)
    process_and_save_response(redis_key, "gender", gender)
    data = redis_instance.hgetall(redis_key)
    log.error(str(data))
    bot.send_message(chat_id, "Nice to meet you {}{}. You are a {} year old {}.".format(get_key(redis_key, 'firstname'),
                                                                                        get_key(redis_key, 'surname'), get_key(redis_key, 'age'), get_key(redis_key, 'gender')))


def process_and_save_response(redis_key, key, value):
    if not redis_instance.exists(redis_key):
        redis_instance.hmset(
            redis_key, {'__start__': datetime.datetime.now().strftime('%s')})
    data = redis_instance.hgetall(redis_key)
    data[key] = value
    redis_instance.hmset(redis_key, data)


def save_args_to_redis(redis_key, **kwargs):
    redis_instance.set(redis_key, json.dumps(kwargs))


def get_key(redis_key, key):
    return str(redis_instance.hget(redis_key, key))


def get_photo_operation(message):
    try:
        chat_id = message.chat.id
        operation = message.text
        if operation not in ("Learn", "Recognise"):
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add('Learn', 'Recognise', 'Do nothing')
            msg = bot.reply_to(
                message, 'What would you like me to do with your photo?', reply_markup=markup)

            bot.register_next_step_handler(msg, get_photo_name)
            return

        file_name = redis_instance.get("{}-facialrecon".format(chat_id))
        if operation == "Learn":
            msg = bot.reply_to(
                message, "I will lable the first person I find in the photo.")
            bot.register_next_step_handler(msg, get_photo_name)
            learn_face.delay(chat_id, file_name, face_name)
            return
        if operation == "Recognise":
            recognise_face.delay(chat_id, file_name)
            return
        bot.send_message(chat_id, 'Ok, nothing will be done')

    except Exception as e:
        log.error(str(e))
        send_system_notification("[tbot] exception",str(e),email=True,send_to_bot=true)


def get_photo_name(message):
    chat_id = message.chat.id
    face_name = message.text
    file_name = redis_instance.get("{}-facialrecon".format(chat_id))
    learn_face.delay(chat_id, file_name, face_name)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text_message(message):
    save_inbound_message.delay(str(message))
    chat_id = message.chat.id
    if message.chat.type == "private":
        if message_contains_youtube_url(message):
            handle_convert_command(message)
            return
    bot.send_message(chat_id, "Reading you 5x5.")


bot.enable_save_next_step_handlers(
    delay=1, filename='{}/step.save'.format(app.config['DOWNLOAD_FOLDER']))
bot.load_next_step_handlers(filename='{}/reply.save'.format(app.config['DOWNLOAD_FOLDER']))
