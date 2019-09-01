import emoji
import traceback
import telegram

from app import app, make_celery, log, mail
from app.auth.models import User, Role
from functools import wraps

def send_typing_action(func):
    """Sends typing action while processing func command."""
    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=telegram.ChatAction.TYPING)        
        return func(update, context,  *args, **kwargs)
    return command_func

celery = make_celery(app)

def error_callback(update, context):    
    if context.error == "Results_too_much":
        send_system_message(bot, err, to_bot=False, also_email=True)    
        return
    log.error("Update {} caused error {}".format(update, context.error))        
    err = traceback.format_exc()
    send_system_message(bot, err, to_bot=True, also_email=True) 

def get_chat_id(update):    
    return update.effective_message.chat_id    

def role_required(required_role):
    def inner_function(f):        
        @wraps(f)
        def wrapper(update, context, *args, **kwargs):
            chat_id = update.effective_message.chat_id        
            user = User.find_by_chatid(chat_id)
            if required_role in user.roles:
                return f(update, context, *args, **kwargs)
            else:
                return update.message.reply_text("You do not have a required role to perform that action.".format(required_role))
        return wrapper
    return inner_function

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
def send_bot_message(bot, chat_id, messageText):
    bot.send_message(chat_id, messageText, disable_web_page_preview=True)

def send_system_message(bot, subject, plainTextMessage=None, email=False, send_to_bot=True):
    if send_to_bot:
        send_bot_message(bot, app.config['ADMIN_CHAT_ID'], emoji.emojize(" :exclamation: {}".format(subject)))
    if email:
        send_email.delay(app.config['NOTIFICATIONS_RECIPIENT_EMAIL'], subject,
                         "Nothing here." if plainTextMessage is None else plainTextMessage, True)
    log.info("{} \t {}".format(subject, plainTextMessage))