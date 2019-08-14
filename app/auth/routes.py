from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_security import login_user, logout_user, login_required, roles_required
from .models import User
import datetime
from app.tasks import send_email, send_bot_message

from app import db, log

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        user = User.query.filter_by(email=email).first()
        if not user or not User.verify_hash(password, user.password):
            flash('User invalid or password incorrect.')
            return redirect(url_for('auth.login'))        
        
        if not user.active:
            flash('You need to enter <a href={}>your confirmation code</a>'.format(url_for('auth.activation')))
            return redirect(url_for('auth.activation'))
        login_user(user, remember=remember)
        return redirect(url_for('main.profile'))
    return render_template('login.html')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            flash('This user already exists!')
            return redirect(url_for('auth.signup'))

        new_user = User(email=email,
                        password=User.generate_hash(password))        
        new_user.save_to_db()
        flash('Ok nearly there, check your email at {} for your confirmation code.'.format(email))
        send_email(email,"DistractoBot confirmation code", "Your confirmation code is {}.".format(new_user.confirmation_code))
        return redirect(url_for('auth.login'))
    return render_template('signup.html')

@auth.route('/activation', methods=['GET','POST'])
def activation():
    if request.method == 'POST':
        confirmation_code = request.form.get('confirmation_code')
        user = User.find_by_email(request.form.get('email'))
        
        if user is not None and user.confirmation_code == confirmation_code:
            user.active = True
            user.email_confirmed_at = datetime.datetime.now()
            user.save_to_db()
            send_bot_message(user.chat_id, 'Thanks, your account is confirmed!')
            login_user(user)
            return redirect(url_for('main.profile'))
    return render_template('activation.html')

@auth.route('/changepassword', methods=['GET','POST'])
@roles_required("admin")
@login_required
def change_password():
    return render_template("changepassword.html")

@auth.route('/users', methods=['GET', 'POST'])
@login_required
def users():    
    users = User.query.all()
    return render_template('users.html', users=users)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
