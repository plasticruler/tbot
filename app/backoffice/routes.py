from flask import Response, Blueprint, render_template, request, redirect, url_for, jsonify, session, make_response, flash
from flask_security import login_required, SQLAlchemySessionUserDatastore, current_user, roles_required
from flask_paginate import Pagination, get_page_args
from app.auth.models import User

from app.tasks import update_reddit_subs_using_payload, send_system_notification, send_email
from app import app, db, log, Config  # , cache

import io
import timeago
import datetime

backoffice = Blueprint('backoffice', __name__)



@backoffice.context_processor
def inject_global():
    return {'app_name':app.config['USER_APP_NAME']}

@backoffice.route('/backoffice')
def landing():
    return render_template('backoffice.html')

@backoffice.route('/')
@login_required
@roles_required('admin')
def system():
    return render_template('admin.html')