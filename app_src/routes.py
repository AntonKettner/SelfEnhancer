from flask import Blueprint, redirect, url_for, render_template
from flask_login import current_user, login_required
from app_src.config import get_api_key

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    api_key = get_api_key()
    return render_template('dashboard.html', 
                         is_admin=current_user.is_admin,
                         api_key_configured=bool(api_key))
