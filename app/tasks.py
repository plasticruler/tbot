# coding: utf-8
from __future__ import unicode_literals
from __future__ import print_function

import json
from urllib import parse
from urllib.parse import urlparse
import redis

import smtplib
import os
import glob
import ssl
import requests
import youtube_dl
from youtube_dl.postprocessor.ffmpeg import FFmpegMetadataPP
import datetime
from app import app, bot, make_celery, log
from app.models import Bot_MessageInbound, Face, Tag, Bot_Quote, EquityPriceSource, EquityInstrument, EquityPrice
from telebot import types
from app.rbot import reddit
import uuid
import time
import datetime
from mp3_tagger import MP3File, VERSION_1, VERSION_2, VERSION_BOTH
from app.utils import get_prices_from_sn


TASK_NOTIFICATION_EMAIL = os.getenv('NOTIFICATIONS_RECIPIENT_EMAIL')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')
GMAIL_ACCOUNT = os.getenv('GMAIL_ACCOUNT')
FROM_ADDRESS = os.getenv('FROM_EMAIL')
REDIS_SERVER = os.getenv('REDIS_SERVER')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
REDIS_PORT = os.getenv('REDIS_PORT')
DOWNLOAD_FOLDER = os.getenv('DOWNLOAD_FOLDER')
WEB_FOLDER = os.getenv('WEB_FOLDER')
BOT_TOKEN = os.getenv('BOT_API_KEY')
HOST_LOCATION = os.getenv('HOST_LOCATION')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')


redis_instance = redis.Redis(
    host=REDIS_SERVER, port=REDIS_PORT, password=REDIS_PASSWORD)


class IllegalArgumentError(ValueError):
    pass


class ThisLogger(object):
    def debug(self, msg):
        log.debug(msg)

    def warning(self, msg):
        log.warning(msg)

    def error(self, msg):
        log.error(msg)


class FFmpegMP3MetadataPP(FFmpegMetadataPP):

    def __init__(self, downloader=None, metadata=None):
        self.metadata = metadata or {}
        super(FFmpegMP3MetadataPP, self).__init__(downloader)

    def run(self, information):
        information = self.purge_metadata(information)
        information.update(self.metadata)
        return super(FFmpegMP3MetadataPP, self).run(information)

    def purge_metadata(self, info):
        info.pop('title', None)
        info.pop('track', None)
        info.pop('upload_date', None)
        info.pop('description', None)
        info.pop('webpage_url', None)
        info.pop('track_number', None)
        info.pop('artist', None)
        info.pop('creator', None)
        info.pop('uploader', None)
        info.pop('uploader_id', None)
        info.pop('genre', None)
        info.pop('album', None)
        info.pop('album_artist', None)
        info.pop('disc_number', None)
        return info


def download_hook(d):
    if d['status'] == 'finished':
        fn = os.path.basename(d['filename'])
        fn = os.path.splitext(fn)[0]
        fn = "{}.{}".format(fn, get_youtube_download_options()[
                            'postprocessors'][0]['preferredcodec'])
        log.info("{} download completed.".format(fn))


def get_youtube_download_options():
    options = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'restrictfilenames': True,
        'outtmpl': '{}%(title)s-%(id)s.%(ext)s'.format(DOWNLOAD_FOLDER),
        'logger': ThisLogger(),
        'progress_hooks': [download_hook],
    }
    return options


celery = make_celery(app)
##############################

@celery.task
def get_photo(chat_id, message_id, file_id, username):
    file_ref = bot.get_file(file_id)
    file_url = "https://api.telegram.org/file/bot{}/{}".format(
        BOT_TOKEN, file_ref.file_path)
    file_name = '{}/{}.jpg'.format(DOWNLOAD_FOLDER, uuid.uuid4().hex)
    response = requests.get(file_url, allow_redirects=True, stream=True)
    with open(file_name, 'wb') as handle:
        for chunk in response.iter_content(chunk_size=512):
            handle.write(chunk)
    send_email.delay(TASK_NOTIFICATION_EMAIL, 'File download task completed',
                     'Someone {} just uploaded a file {}'.format(username, file_name))
    bot.reply_to(fakeMessage(chat_id, message_id),
                 "Ok one moment while I scan your image.")
    recognise_face.delay(chat_id, file_name)
    redis_instance.set('{}-facialrecon'.format(chat_id), file_name)
###########################################

def fakeMessage(chat_id, message_id):
    class C:
        def __init__(self, chat_id):
            self.id = chat_id

    class M:
        def __init__(self, chat_id, message_id):
            self.chat = C(chat_id)
            self.message_id = message_id
    return M(chat_id, message_id)
###########################################  

@celery.task
def recognise_face(chat_id, file_name):
    bot.send_message(
        chat_id, 'Ok, please wait. Do not send another picture in the meantime.')
    import face_recognition
    faces = Face().query.all()
    recognised_faces = []

    for face in faces:
        face_encoding = [float(x) for x in face.face_encoding.split('@')]
        img = face_recognition.load_image_file(file_name)
        target_encodings = face_recognition.face_encodings(img)
        if len(target_encodings) > 0:
            for target_encoding in target_encodings:
                match_results = face_recognition.compare_faces(
                    [face_encoding], target_encoding)
                if match_results[0]:
                    recognised_faces.append(face.person_name)
    bot.send_message(chat_id, "Recognised {}".format(
        ", ".join(recognised_faces) if len(recognised_faces) > 0 else "noburry."))
    send_email.delay(TASK_NOTIFICATION_EMAIL, "Facial recon results",
                     "In photo {} recognised {}".format(file_name, ", ".join(recognised_faces)))
###########################################

@celery.task
def learn_face(chat_id, file_name, name):
    import face_recognition
    bot.send_message(chat_id, 'Face recognition starting...')
    img = face_recognition.load_image_file(file_name)
    clooney_encoding = face_recognition.face_encodings(img)[0]
    face = Face()
    face.person_name = name
    face.face_encoding = "@".join([str(x) for x in clooney_encoding])
    face.save_to_db()
    bot.send_message(
        chat_id, 'Facial parameters for {} saved to db.'.format(name))
###########################################

@celery.task
def save_inbound_message(message):
    im = Bot_MessageInbound(content=message)
    im.save_to_db()
###########################################

@celery.task
def download_youtube(chatid, url, arguments_as_dict):
    log.info("Getting ready to download {}".format(url))
    kwargs = json.loads(arguments_as_dict)
    if 'proc_status' not in kwargs:
        kwargs['proc_status_'] = 'received'
    kwargs['proc_status_'] = 'received'
    redis_instance.set(chatid, json.dumps(kwargs))
    kwargs['proc_status'] = 'metadata'
    r = requests.get(
        "https://www.youtube.com/oembed?url={}&format=json".format(url))
    youtube_data = json.loads("["+r.text+"]")[0]
    metadata = {}
    metadata['artist'] = youtube_data['author_name']
    metadata['title'] = youtube_data['title']
    metadata['webpage_url'] = youtube_data['author_url']
    bot.send_message(chatid, 'Ok. Your file is being processed')
    with youtube_dl.YoutubeDL(get_youtube_download_options()) as ydl:
        ffmpeg_mp3_metadata_pp = FFmpegMP3MetadataPP(ydl, metadata)
        ydl.add_post_processor(ffmpeg_mp3_metadata_pp)
        ydl.download([url])
    kwargs['proc_status_'] = 'done'
    send_email.delay(kwargs['email'] if 'email' in kwargs['email'] else TASK_NOTIFICATION_EMAIL, 'Task completed - {}'.format(
        kwargs['youtube_url']), 'Username "{}" triggered a conversion which just completed.'.format(kwargs['username']))
    # locate file with youtube_id in name
    os.chdir(DOWNLOAD_FOLDER)
    for file in glob.glob('*{}*.mp3'.format(kwargs['youtube_id'])):
        # move the file
        os.rename("{}{}".format(DOWNLOAD_FOLDER, file), "{}{}".format(
            WEB_FOLDER, file))  # do you want to be a bad ass?
        download_url = "{}{}".format(HOST_LOCATION, file)
        bot.send_message(
            chatid, 'Processing completed! Your file is at {}'.format(download_url))
        send_bot_message.delay(ADMIN_CHAT_ID, "Youtube download completed for {}. File is at {}".format(
            kwargs['username'], download_url))
    redis_instance.set(chatid, json.dumps(kwargs))
###########################################

@celery.task
def update_reddit_subs_from_title(subreddit, top_of='week', limit=50, prefix=None):
    send_system_notification(
        'Starting update for {}...'.format(subreddit), email=True)
    sr = reddit.subreddit(subreddit).top(top_of, limit=limit)
    titles = [post.title for post in sr if not post.stickied]
    prefix_ = "" if prefix is None else " ({})".format(prefix)
    for t in titles:
        bq = Bot_Quote(text="{}{}".format(t, prefix_))
        bq.tags = [subreddit]
        bq.save_to_db()
    send_system_notification(

        'Update for {} successful.'.format(subreddit), email=True)
###########################################

@celery.task
def update_reddit_subs_using_payload(subreddit, top_of='month', limit=50):
    send_system_notification(
        'Starting full update for {}...'.format(subreddit), email=True)
    sr = reddit.subreddit(subreddit).top(top_of, limit=limit)
    posts = [{'id': post.id, 'title': post.title, 'selftext': post.selftext, 'url': post.url, 'media': post.media,
              'is_reddit_media_domain': post.is_reddit_media_domain, 'thumbnail': post.thumbnail, 'thumbnail_width': post.thumbnail_width,
              'thumbnail_height': post.thumbnail_height} for post in sr if not post.stickied]
    for post in posts:
        bq = Bot_Quote(text=json.dumps(post))
        bq.tags = [subreddit, '_fullpayload']
        bq.save_to_db()
        #if '.jpg' in post['url']:
        #    save_file_name = DOWNLOAD_FOLDER + \
        #        get_filename_from_url(post['url'])
        #    download_file.delay(post['url'], save_file_name)
    send_system_notification(
        'Full update for {} successful.'.format(subreddit), email=True)
############################################

@celery.task
def update_multiple_reddit_subs_using_payload(subredditlist, top_of='month', limit=500):
    for subreddit in subredditlist.split(','):
        update_reddit_subs_using_payload.delay(subreddit, top_of, limit)
############################################

@celery.task
def update_multiple_reddit_subs_using_title(subredditlist, top_of='month', limit=500):
    for subreddit in subredditlist.split(','):
        update_reddit_subs_from_title(
            subreddit, top_of, limit, prefix=subreddit)
############################################

def get_filename_from_url(url):
    a = urlparse(url)
    return os.path.basename(a.path)
############################################

@celery.task
def tag_mp3(file_name, **kwargs):
    valid_tags = ['album', 'song', 'artist', 'comment', 'year', 'genre']
    mp3 = MP3File(file_name)
    tags = mp3.get_tags()
    mp3.save()
############################################

def get_default_browser_headers(**kwargs):
    d = {}
    if "headers" in kwargs:
        d = kwargs["headers"]
    if "User-Agent" not in d:
        d["User-Agent"] = "Mozilla/5.0"
    return d
###########################################

@celery.task
def post_to_url(url, **kwargs):
    values = json.dumps(dict(**kwargs))
    result = 500
    try:
        with requests.Session() as s:
            s.headers = get_default_browser_headers()
            s.headers.add("X-Internal-Secret", "PASS")
            s.post(url, data=values)
            return s.status_code
    except Exception as e:
        send_email.delay(TASK_NOTIFICATION_EMAIL,
                         'Post to url failed. {}'.format(url), e)
###########################################

@celery.task
def download_share_prices():
    sources = EquityPriceSource.query.filter_by(is_active=True)
    for source in sources: #actualy what we need here is a plugin that gets activated
        if not source.source_key == 'SHN':
            continue
        log.info("Running source: {}".format(source.source_name))
        tracked_instruments = EquityInstrument.query.filter_by(is_active=True)
        for ins in tracked_instruments:
            log.info("Downloading price data for {}.".format(ins.jse_code))
            fname = "{}{}-{}-{}.sd-snapshot".format(DOWNLOAD_FOLDER, time.time(), ins.jse_code, source.source_key)
            download_file.delay(source.data1.format(ins.jse_code), fname)

@celery.task
def process_shareprice_data():
    for f in glob.glob('{}*SHN.sd-snapshot'.format(DOWNLOAD_FOLDER)):
        price_source = EquityPriceSource.find_by_source_key('SHN')
        code = f.split('-')[1]        
        equity_instrument = EquityInstrument.find_by_code(code)        
        dt = datetime.datetime.fromtimestamp(int(f.split('.')[0].split('/')[-1]))
        price_data = get_prices_from_sn(f)
        equity_price = EquityPrice()
        equity_price.buy_offer_price = price_data['buy_offer_price']
        equity_price.downloaded_timestamp = dt
        equity_price.deal_count = price_data['deal_count']
        equity_price.from_52_week_high = price_data['from_52_week_high']
        equity_price.from_52_week_low = price_data['from_52_week_low']
        equity_price.price_move = price_data['price_move']
        equity_price.last_sales_price = price_data['last_sales_price']
        equity_price.sell_offer_price = price_data['sell_offer_price']
        equity_price.today_high = price_data['today_high']
        equity_price.today_low = price_data['today_low']
        equity_price.volume_count = price_data['volume_count']
        equity_price.deals_value = price_data['deals_value']   
        equity_price.equityinstrument = equity_instrument
        equity_price.equityinstrument_id = equity_instrument.id    
        equity_price.equitypricesource_id = price_source.id 
        equity_price.equitypricesource = price_source 
        equity_price.save_to_db()
        os.remove(f)
        log.info('Processed file {}'.format(f))
    
###########################################

def is_video_related_post(payload):
    pattern = 'https://v.redd.it/[a-zA-Z0-9]{13}'
    url = payload['url']
    if not re.match(pattern, url):
        return False
    if 'media' in payload:
        media = payload['media']
        if media is not None and 'reddit_video' in media:
            reddit_video = media['reddit_video']
            if reddit_video is not None and reddit_video['is_gif']:
                return True
    if url.startswith('https://v.redd.it') or url.endswith('gif') or url.startswith('https://gfycat.com/') or url.endswith('gifv') or url.endswith('mp4'):                
        return True
    return False

@celery.task
def send_random_quote(chat_id):
    payload = Bot_Quote().return_random()['quotes']
    if "media" not in payload['quote']:
        bot.send_message(chat_id, "{} ({})".format(
            payload['quote'], payload['id']))
        return
    else:
        jpayload = json.loads(payload['quote'])
        url = jpayload['url']
        if is_video_related_post(jpayload):                
            bot.send_video(chat_id, url, caption="{} ({})".format(jpayload['title'], payload['id']))
            return    
        bot.send_photo(chat_id, url, caption="{} ({})".format(jpayload['title'], payload['id']))
###########################################
@celery.task
def send_uptime_message():
    send_random_quote.delay()
    #send_system_notification.delay("System is up and running.")
###########################################

@celery.task
def download_file(url, destination, **kwargs):
    headers = {}
    if "headers" not in kwargs:
        headers = get_default_browser_headers()
    else:
        headers = headers
    r = requests.get(url, headers=headers)
    try:
        with open(destination, 'wb') as f:
            for chunk in r.iter_content(chunk_size=512):
                f.write(chunk)
    except Exception as e:
        send_email.delay(TASK_NOTIFICATION_EMAIL, 'Task failure', e)
    return r.status_code
##########################################

@celery.task
def send_system_notification(subject, plainTextMessage=None, email=False, send_to_bot=True):
    if send_to_bot:
        send_bot_message.delay(ADMIN_CHAT_ID, subject)
    if email:
        send_email.delay(TASK_NOTIFICATION_EMAIL, subject,
                         "Nothing here." if plainTextMessage is None else plainTextMessage, True)
    log.info("{} \t {}".format(subject, plainTextMessage))
#########################################

@celery.task
def send_bot_message(chat_id, messageText):
    bot.send_message(chat_id, messageText)
##########################################

@celery.task
def send_email(to, subject, plaintextMessage, deletable=True):
    smtp_server = "smtp.gmail.com"
    port = 465
    context = ssl.create_default_context()
    subject = "{}".format(subject + " <deletable>" if deletable else subject)
    try:
        receiver_email = to
        message = "Subject: {} \n\n {}".format(subject, plaintextMessage)
        server = smtplib.SMTP_SSL(smtp_server, port)
        server.ehlo()
        server.login(GMAIL_ACCOUNT, GMAIL_PASSWORD)
        server.sendmail(FROM_ADDRESS, TASK_NOTIFICATION_EMAIL, message)
        server.quit()
        print("Email '{}' to {} sent.".format(subject, to))
    except Exception as e:
        log.error(e)      
