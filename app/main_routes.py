from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from .models import User, EquityInstrument,  KeyValueEntry, Key, UserSubscription

from app import app, db, log

import telebot

main = Blueprint('main', __name__)

@app.before_first_request
def create_tables():
    db.create_all()

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile', methods = ['GET','POST'])
@login_required
def profile():

    if request.method == 'GET':
        id_to_delete = request.args.get('id')
        log.info("Id to delete: {}".format(id_to_delete))
        if id_to_delete is not None:
            sub_to_delete = UserSubscription.query.get(id_to_delete)
            if sub_to_delete is not None:
                db.session.delete(sub_to_delete)
                db.session.commit()                        
                redirect(url_for('main.profile'))

    #person enters the keyvalue_entry
    #which must be associated to a key (to get media type)
    if request.method == 'POST':
        kvn = request.form.get('subreddit_name')
        log.info(request.form)
        kvn = kvn.strip()
        k = 'sr_media' #always assume it's media related        
        key = Key.find_by_name(k)
        if (key is None):
            key = Key()
            key.name = k
            key.save_to_db()
        kv = KeyValueEntry.find_by_key_value(k, kvn)
        if kv is None:            
            kv = KeyValueEntry()
            kv.key = key
            kv.value = kvn
            kv.save_to_db()
        sub = UserSubscription()
        sub.user_id = current_user.id
        sub.content_id = kv.id
        sub.save_to_db()        
        return redirect(url_for('main.profile'))   
    subscriptions = UserSubscription.get_by_user(user_id=current_user.id)
    return render_template('profile.html', subscriptions=subscriptions, email_address=current_user.email)
   
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
