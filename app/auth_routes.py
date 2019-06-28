from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from .models import User

from app import db

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

        return redirect(url_for('auth.login'))
    return render_template('signup.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
