from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from .models import User, APIKey, db

auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_api_key():
    api_key = APIKey.query.first()
    return api_key.openai_key if api_key else None

@auth_bp.route('/login', methods=['GET', 'POST'])
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

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/api-key', methods=['GET', 'POST'])
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
    
    api_key = get_api_key()
    masked_key = f"{api_key[:10]}..." if api_key else None
    return render_template('api_key.html', api_key=masked_key)

@auth_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    if request.method == 'POST':
        username = request.form.get('username')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect')
            return redirect(url_for('auth.user_settings'))
        
        if username and username != current_user.username:
            if User.query.filter_by(username=username).first():
                flash('Username already exists')
                return redirect(url_for('auth.user_settings'))
            current_user.username = username
        
        if new_password:
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('Settings updated successfully')
        return redirect(url_for('main.dashboard'))
    
    return render_template('settings.html', user=current_user)

def init_db(app):
    """Initialize the database and create admin user"""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        # Create admin user if it doesn't exist
        if not User.query.filter_by(username='admin').first():
            print("Creating admin user...")
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully")
