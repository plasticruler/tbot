import datetime
import json
import os
import random
import re
import uuid
from urllib import parse

import redis
import requests
from telebot import types
import re

from app import bot, log
from app.models import Bot_Quote, SelfLog
from app.tasks import download_youtube, learn_face, recognise_face, save_inbound_message, send_email, send_random_quote

REDIS_SERVER = os.getenv('REDIS_SERVER')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
REDIS_PORT = os.getenv('REDIS_PORT')
ADMIN_EMAIL = os.getenv('NOTIFICATIONS_RECIPIENT_EMAIL')
BOT_API_KEY = os.getenv('BOT_API_KEY')
ADMIN_EMAIL = os.getenv('NOTIFICATIONS_RECIPIENT_EMAIL')
DOWNLOAD_FOLDER = os.getenv('DOWNLOAD_FOLDER')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

redis_instance = redis.Redis(host=REDIS_SERVER, port=REDIS_PORT,
                             password=REDIS_PASSWORD, charset='utf-8', decode_responses=True)

authorised_usernames = os.getenv('AUTHORIZED_USERNAMES').split(',')



# BOT RELATED
@bot.message_handler(commands=['help', 'start', 'convert', 'quote', '8ball', 'register','slog'])
def send_welcome(message):
    save_inbound_message.delay(str(message))
    chat_id = message.chat.id
    if "/quote" in message.text:
        send_random_quote.delay(chat_id)
    elif "/register" in message.text:
        msg = bot.reply_to(
            message, "This is the registration step. What is your surname?")
        redis_key = "{}-register".format(chat_id)
        process_and_save_response(
            redis_key, "firstname", message.from_user.first_name)
        bot.register_next_step_handler(msg, process_surname_step)
    elif "/slog" in message.text:
        if message.chat.type == "private":
            sl = SelfLog()
            sl.chat_id = chat_id
            sl.message = message.text
            sl.save_to_db()
            bot.reply_to(message, 'Ok')
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
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
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


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if not message.chat.type == "private" or message.from_user.is_bot:
        return
    chat_id = message.chat.id
    save_inbound_message.delay(str(message))
    file_ref = bot.get_file(message.photo[-1].file_id)
    file_url = "https://api.telegram.org/file/bot{}/{}".format(
        BOT_API_KEY, file_ref.file_path)
    file_name = "{}/{}.jpg".format(DOWNLOAD_FOLDER, uuid.uuid4().hex)
    redis_instance.set("{}-fr-filename".format(chat_id), file_name)
    response = requests.get(file_url, allow_redirects=True, stream=True)
    username = message.from_user.username
    bot.send_message(
        ADMIN_CHAT_ID, "User {} is initiating a face operation.".format(username))
    bot.forward_message(ADMIN_CHAT_ID, chat_id, message.message_id)
    send_email.delay(
        ADMIN_EMAIL, "User {} is using face RECON".format(username), "None")
    with open(file_name, 'bw+') as handle:
        for chunk in response.iter_content(chunk_size=512):
            handle.write(chunk)
    send_email.delay(ADMIN_EMAIL, "A photo has been uploaded",
                     "{} just uploaded a file {}.".format(username, file_name))
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Learn', 'Recognise', 'Do nothing')
    msg = bot.reply_to(
        message, "What would you like me to do with your photo?", reply_markup=markup)
    bot.register_next_step_handler(msg, get_photo_processing_command)


def get_photo_processing_command(message):
    command = message.text
    chat_id = message.chat.id
    file_name = redis_instance.get("{}-fr-filename".format(chat_id))
    if command not in ('Learn', 'Recognise'):
        bot.send_message(chat_id, 'Ok, I will no nothing.')
        return
    if command == 'Recognise':
        recognise_face.delay(chat_id, file_name)
    else:
        bot.send_message(ADMIN_CHAT_ID, "User {} has opted to do face recon on {}".format(
            message.from_user.username, file_name))
        msg = bot.reply_to(
            message, "Ok, I'll use whatever you type next as the name of the first face I see.")
        bot.register_next_step_handler(msg, get_face_name)


def get_face_name(message):
    face_name = message.text
    chat_id = message.chat.id
    file_name = redis_instance.get("{}-fr-filename".format(chat_id))
    bot.reply_to(
        message, "Ok I'll use the name {} to describe this face next time I see it".format(face_name))
    learn_face.delay(chat_id, file_name, face_name)
    bot.send_message(chat_id, "Your face learning task will begin now...")

########################


def get_photo_operation(message):
    try:
        chat_id = message.chat.id
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Learn', 'Recognise', 'Do nothing')
        msg = bot.reply_to(
            message, 'I can try and recognise or learn faces in the photo. What should I do?', reply_markup=markup)
        bot.register_next_step_handler(msg, process_photo_operation_step)
    except Exception as e:
        bot.reply_to(message, 'oops')


def process_surname_step(message):
    try:
        chat_id = message.chat.id
        surname = message.text
        redis_key = "{}-register".format(chat_id)
        process_and_save_response(redis_key, "surname", surname)
        msg = bot.reply_to(message, "And how old are you?")
        bot.register_next_step_handler(msg, process_age_step)
    except Exception as e:
        log.error(str(e))
        bot.reply_to(message, 'oops')


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
        bot.reply_to(message, 'oops')


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
        print("In get_photo_operation")
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
        bot.reply_to(message, 'oops')


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
    delay=1, filename='{}/step.save'.format(DOWNLOAD_FOLDER))
bot.load_next_step_handlers(filename='{}/reply.save'.format(DOWNLOAD_FOLDER))
