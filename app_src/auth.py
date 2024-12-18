from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from app_src.models import User, db, APIKey

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    if request.method == 'POST':
        username = request.form.get('username')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        # Verify current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect')
            return redirect(url_for('auth.user_settings'))
        
        # Update username if provided and different
        if username and username != current_user.username:
            # Check if username is already taken
            if User.query.filter_by(username=username).first():
                flash('Username already exists')
                return redirect(url_for('auth.user_settings'))
            current_user.username = username
        
        # Update password if provided
        if new_password:
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('Settings updated successfully')
        return redirect(url_for('main.dashboard'))
    
    return render_template('settings.html', user=current_user)

@auth.route('/api-key', methods=['GET', 'POST'])
@login_required
def manage_api_key():
    if not current_user.is_admin:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        new_key = request.form.get('api_key')
        if new_key:
            api_key = APIKey.query.first()
            if api_key:
                api_key.openai_key = new_key
            else:
                api_key = APIKey(openai_key=new_key)
                db.session.add(api_key)
            db.session.commit()
            flash('API key updated successfully')
            return redirect(url_for('main.dashboard'))
    
    api_key = APIKey.query.first()
    # Show first 10 digits of API key if it exists
    masked_key = f"{api_key.openai_key[:10]}..." if api_key else None
    return render_template('api_key.html', api_key=masked_key)
