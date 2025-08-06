from app.models import User
from app.models import Device
from app.models import Interface
from app.extensions import db
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.forms import LoginForm
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

main = Blueprint('main', __name__)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index')) 
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Zalogowano pomyślnie!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Nieprawidłowa nazwa użytkownika lub hasło.', 'danger')
    return render_template('login.html', form=form)

@main.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        devices = Device.query.all()
        return render_template('main.html', devices=devices )
    else:
        return redirect(url_for('main.login'))
@main.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('Wylogowano.', 'info')
    return redirect(url_for('main.index'))
