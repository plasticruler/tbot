# coding: utf-8
from app import app, bot, log, BOT_SECRET, BOT_API_KEY, db
from flask import request
from app import tasks
import telebot

import os
# flask related routes
@app.route('/{}'.format(BOT_SECRET), methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(
        request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'ok'

@app.route('/echo')
def echo():
    return 'Hello you.', 200

@app.before_first_request
def create_tables():
    db.create_all()
