from flask import Response, Blueprint, render_template, request, redirect, url_for,jsonify, make_response, flash
from flask_security import login_required, SQLAlchemySessionUserDatastore, current_user, roles_required
from flask_paginate import Pagination, get_page_args
from .models import EquityInstrument,  KeyValueEntry, Key, UserSubscription
from app.auth.models import User
from app.tasks import send_random_quote, update_reddit_subs_using_payload, send_system_notification
from app import app, db, log, Config

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
import telebot

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/system')
@login_required
@roles_required('admin')
def system():
    return render_template('admin.html')

@main.route('/sendsystemmessage')
@roles_required('admin')
@login_required
def send_system_message():
    send_system_notification("Test message subject", "Nothing to see here", True, True)
    return make_response('Ok',200)

@main.route('/resendactivationemail')
@login_required
@roles_required('admin')
def resend_activation_email():
    identifier = request.args.get('identifier')
    identifier_type = request.args.get('idtype')    
    return make_response('Ok', 200)


@main.route('/refreshcontent/<r>', methods=['GET'])
@roles_required('admin')
@login_required
def refresh_content(r='d'):
    if current_user.is_authenticated and current_user.is_active:
        update_reddit_subs_using_payload.delay(r,limit=500)
        return make_response('Ok: ', r,200)
    else:
        return make_response('No', 403)

@main.route('/sendrandom', methods=['GET'])
@login_required
def send_random():
    if current_user.is_authenticated and current_user.is_active:
        send_random_quote.delay(current_user.chat_id)
        return make_response('Ok',200)
    else:
        return make_response('Computer says no',403)

@main.route('/userprofile/<userid>')
@login_required
@roles_required('admin')
def userprofile(userid):
    usr = User.query.get(userid)
    if usr is None:
        flash('Invalid user.')
        return redirect(url_for('auth.users'))
    subscriptions = UserSubscription.get_by_user(userid)
    return render_template('userprofile.html', user=usr, subscriptions=subscriptions)

@main.route('/profile', methods = ['GET','POST'])
@login_required
def profile():    
    if request.method == 'GET':
        id_to_delete = request.args.get('id')        
        if id_to_delete is not None:
            sub_to_delete = UserSubscription.get_by_id_for_user(id_to_delete, current_user.id)
            if sub_to_delete is not None:                
                sub_to_delete.delete()                      
                return redirect(url_for('main.profile'))                        

    #person enters the keyvalue_entry
    #which must be associated to a key (to get media type)
    if request.method == 'POST':
        if not len(request.form.get('subreddit_name').strip())==0:            
            usr = User.query.get(current_user.id)        
            sub = request.form.get('subreddit_name').strip()
            kvn = sub.strip()
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
    subscriptions = UserSubscription.get_by_user(user_id=current_user.id)
    return render_template('profile.html', subscriptions=subscriptions, email_address=current_user.email)
   
@main.route('/subreddits', methods=['GET', 'POST'])
@roles_required('admin')
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


@main.route('/instruments', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def instruments():    
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')      
    instruments = EquityInstrument.query.offset((page-1)*per_page).limit(per_page)        
    instrument_count = EquityInstrument.query.count()    
    pagination = Pagination(page=page, per_page=per_page, total=instrument_count)            
    return render_template('instruments.html', instruments=instruments, page=page, per_page=per_page, pagination=pagination)

    
@main.route('/schedules', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def schedules():
    return render_template('schedules.html')

@main.route('/stats', methods=['GET'])
@login_required
@roles_required('admin')
def stats():
    return render_template('stats.html')

#select t.name, count(bq.id) from content_stats cs join bot_quote bq on bq.id=cs.quote_id join tag_associations ta on ta.bot_quote_id=bq.id join tag t on t.id=ta.tag_id where t.name not like '%\_%' and user_id=15 group by t.name order by count(bq.id) desc limit 10;
@main.route('/plotcontent/<user_id>/<record_limit>', methods=['GET'])
@roles_required('admin')
@login_required
def plotbycontentcount(user_id, record_limit):
    fig = create_figure(current_user.id, record_limit)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')
def create_figure(user_id=None, record_limit=10):
    fig = Figure()
    axis = fig.add_subplot(1,1,1)
    if user_id is not None:
        s = "select t.name, count(bq.id) from content_stats cs join bot_quote bq on bq.id=cs.quote_id join tag_associations ta on ta.bot_quote_id=bq.id join tag t on t.id=ta.tag_id where t.name not like '%%" + "\_%%' and user_id={} group by t.name order by count(bq.id) desc limit {};".format(user_id, record_limit)        
        distributions = db.engine.execute(s)
    else:
        distributions = db.engine.execute("select t.name, count(bq.id) from content_stats cs join bot_quote bq on bq.id=cs.quote_id join tag_associations ta on ta.bot_quote_id=bq.id join tag t on t.id=ta.tag_id where t.name not like '%\\_%' group by t.name order by count(bq.id) desc limit 10;")
    distributions = dict(list(distributions))
    counts = [x for x in distributions.values()]
    labels = [y for y in distributions.keys()]
    axis.pie(counts, labels=labels,shadow=True, startangle=90 )
    return fig
