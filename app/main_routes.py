from flask import Blueprint, render_template, request, redirect, url_for,jsonify
from flask_login import login_required, current_user
from flask_paginate import Pagination, get_page_args
from .models import User, EquityInstrument,  KeyValueEntry, Key, UserSubscription
from .schedule_models import Parameter, ConfiguredTask
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
        if id_to_delete is not None:
            sub_to_delete = UserSubscription.query.get_by_id_for_user(id_to_delete, current_user.id)
            if sub_to_delete is not None:
                db.session.delete(sub_to_delete)
                db.session.commit()                        
                redirect(url_for('main.profile'))

    #person enters the keyvalue_entry
    #which must be associated to a key (to get media type)
    if request.method == 'POST':
        usr = User.query.get(current_user.id)
        usr.add_sub(request.form.get('subreddit_name').strip())        
        return redirect(url_for('main.profile'))   
    subscriptions = UserSubscription.get_by_user(user_id=current_user.id)
    return render_template('profile.html', subscriptions=subscriptions, email_address=current_user.email)
   
@main.route('/subreddits', methods=['GET', 'POST'])
@login_required
def subreddits():    
    reddits = None        
    if request.method == 'GET':        
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')            
        reddits = KeyValueEntry.query.join(Key, KeyValueEntry.key).filter(Key.name.in_(['sr_media','sr_title'])).order_by(KeyValueEntry.value).offset((page-1) * per_page).limit(per_page)        
        reddits_count = KeyValueEntry.query.join(Key, KeyValueEntry.key).filter(Key.name.in_(['sr_media','sr_title'])).count()
        log.info("reddits_count {}".format(reddits_count))
        pagination = Pagination(page=page, per_page=per_page, total=reddits_count)
        return render_template('subreddits.html', reddits=reddits, page=page,per_page=per_page, pagination=pagination)

    return render_template('subreddits.html', reddits=reddits)

@main.route('/api/subreddits/<q>', methods=['GET'])
def instruments_get(q):
    reddits = KeyValueEntry.query.join(Key, KeyValueEntry.key).filter(Key.name.in_(['sr_media','sr_title'])).filter(KeyValueEntry.value.like('%{}%'.format(q))).order_by(KeyValueEntry.value)                
    reddits = [r.value for r in reddits]
    return jsonify(reddits)

@main.route('/instruments', methods=['GET', 'POST'])
@login_required
def instruments():    
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')  
    log.info('offset {}'.format(offset))      
    log.info('page: {}'.format(page))
    instruments = EquityInstrument.query.offset((page-1)*per_page).limit(per_page)        
    instrument_count = EquityInstrument.query.count()    
    pagination = Pagination(page=page, per_page=per_page, total=instrument_count)            
    return render_template('instruments.html', instruments=instruments, page=page, per_page=per_page, pagination=pagination)

    
@main.route('/schedules', methods=['GET', 'POST'])
@login_required
def schedules():
    return render_template('schedules.html')


