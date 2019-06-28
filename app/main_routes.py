from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from .models import EquityInstrument,  KeyValueEntry

from app import app, db

import telebot

main = Blueprint('main', __name__)

@app.before_first_request
def create_tables():
    db.create_all()

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', email_address=current_user.email)


@main.route('/subreddits', methods=['GET', 'POST'])
@login_required
def subreddits():
    reddits = None
    if request.method == 'GET':
        reddits = KeyValueEntry.get_by_key('sr_media').union(
            KeyValueEntry.get_by_key('sr_title')).order_by(KeyValueEntry.value)
    return render_template('subreddits.html', reddits=reddits)


@main.route('/instruments', methods=['GET', 'POST'])
@login_required
def instruments():
    instruments = None
    if request.method == 'GET':
        instruments = EquityInstrument.query.all()
    return render_template('instruments.html', instruments=instruments)
