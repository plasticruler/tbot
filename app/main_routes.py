from flask import Blueprint, render_template, request, redirect, url_for,jsonify, make_response
from flask_login import login_required, current_user
from flask_paginate import Pagination, get_page_args
from .models import User, EquityInstrument,  KeyValueEntry, Key, UserSubscription
from .schedule_models import Parameter, ConfiguredTask
from app.tasks import send_random_quote, update_reddit_subs_using_payload
from app import app, db, log

import telebot

main = Blueprint('main', __name__)

@app.before_first_request
def create_tables():
    db.create_all()

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/refreshcontent/<r>', methods=['GET'])
def refresh_content(r='d'):
    if current_user.is_authenticated and current_user.is_active:
        update_reddit_subs_using_payload.delay(r,limit=500)
        return make_response('Ok: '+ r,200)
    else:
        return make_response('Auth required', 403)

@main.route('/sendrandom', methods=['GET'])
def send_random():
    if current_user.is_authenticated and current_user.is_active:
        send_random_quote.delay(current_user.chat_id)
        return make_response('Ok',200)
    else:
        return make_response('Auth required',403)


@main.route('/profile', methods = ['GET','POST'])
@login_required
def profile():
    log.debug('profile view loaded')
    if request.method == 'GET':
        id_to_delete = request.args.get('id')
        log.debug('id to delete: '+str(id_to_delete))
        if id_to_delete is not None:
            sub_to_delete = UserSubscription.get_by_id_for_user(id_to_delete, current_user.id)
            if sub_to_delete is not None:
                log.debug('Going to delete ' + str(sub_to_delete.id))
                sub_to_delete.delete()      
                log.info('subscription deleted')
                return redirect(url_for('main.profile'))                        

    #person enters the keyvalue_entry
    #which must be associated to a key (to get media type)
    if request.method == 'POST':
        if not len(request.form.get('subreddit_name').strip())==0:
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
        reddit_content_count = db.engine.execute("select tag.name, count(*) from bot_quote join tag_associations on bot_quote_id=bot_quote.id join tag on tag.id=tag_associations.tag_id group by tag.name;")
        reddit_content_count = dict(list(reddit_content_count))
        reddits_count = KeyValueEntry.query.join(Key, KeyValueEntry.key).filter(Key.name.in_(['sr_media','sr_title'])).count()        
        pagination = Pagination(page=page, per_page=per_page, total=reddits_count)
        return render_template('subreddits.html', reddits=reddits, page=page,per_page=per_page, pagination=pagination, rc=reddit_content_count)

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
    instruments = EquityInstrument.query.offset((page-1)*per_page).limit(per_page)        
    instrument_count = EquityInstrument.query.count()    
    pagination = Pagination(page=page, per_page=per_page, total=instrument_count)            
    return render_template('instruments.html', instruments=instruments, page=page, per_page=per_page, pagination=pagination)

    
@main.route('/schedules', methods=['GET', 'POST'])
@login_required
def schedules():
    return render_template('schedules.html')


