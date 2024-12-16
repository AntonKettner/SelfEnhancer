__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from enhancer import Enhancement
from io import StringIO
from threading import Thread
import queue

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("No SECRET_KEY set for Flask application")

# Use absolute path for SQLite database in Azure
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:////home/data/users.db')

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    openai_key = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_api_key():
    api_key = APIKey.query.first()
    return api_key.openai_key if api_key else None

def capture_output(queue):
    old_stdout = sys.stdout
    redirected_output = StringIO()
    sys.stdout = redirected_output

    try:
        # Set OpenAI API key from database
        api_key = get_api_key()
        if not api_key:
            queue.put("Error: OpenAI API key not configured")
            return

        os.environ['OPENAI_API_KEY'] = api_key
        
        enhancement = Enhancement()
        enhancement.ideas, enhancement.usage = enhancement.generate_improvement_ideas()
        
        # Format the output
        output = "IDEAS FOR CODEBASE ENHANCEMENT:\n\n"
        for index, idea in enumerate(enhancement.ideas):
            output += f"{index+1}: {idea}\n\n"
        output += f"\nAPI Usage:\n{enhancement.usage}"
        
        queue.put(output)
    finally:
        sys.stdout = old_stdout

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    api_key = get_api_key()
    return render_template('dashboard.html', 
                         is_admin=current_user.is_admin,
                         api_key_configured=bool(api_key))

@app.route('/api-key', methods=['GET', 'POST'])
@login_required
def manage_api_key():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
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
            return redirect(url_for('dashboard'))
    
    api_key = get_api_key()
    return render_template('api_key.html', api_key=api_key)

@app.route('/run-enhancement')
@login_required
def run_enhancement():
    def generate():
        output_queue = queue.Queue()
        thread = Thread(target=capture_output, args=(output_queue,))
        thread.start()
        
        while True:
            try:
                output = output_queue.get(timeout=1)
                yield f"data: {output}\n\n"
                break
            except queue.Empty:
                yield "data: Processing...\n\n"
            
            if not thread.is_alive():
                break
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create a default admin user if none exists
        if not User.query.filter_by(username='admin').first():
            user = User(username='admin', is_admin=True)
            user.set_password('admin')
            db.session.add(user)
            db.session.commit()
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
