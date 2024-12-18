__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import shutil
import tempfile
import zipfile
from enhancer import Enhancement
from io import StringIO
from threading import Thread
import queue
import traceback

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("No SECRET_KEY set for Flask application")

# Use Azure Web App's persistent storage for SQLite database
default_db_path = 'sqlite:////home/site/wwwroot/data/sqlite/users.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', default_db_path)

# Ensure database directory exists
db_dir = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
os.makedirs(db_dir, exist_ok=True)
os.chmod(db_dir, 0o755)

# Configure upload settings - store in project directory
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'data', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    __tablename__ = 'users'  # Explicitly set table name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class APIKey(db.Model):
    __tablename__ = 'api_keys'  # Explicitly set table name
    id = db.Column(db.Integer, primary_key=True)
    openai_key = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_api_key():
    api_key = APIKey.query.first()
    return api_key.openai_key if api_key else None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'zip', 'py', 'txt', 'md'}

class OutputCapture:
    def __init__(self, queue):
        self.queue = queue
        self.buffer = StringIO()

    def write(self, text):
        self.buffer.write(text)
        if '\n' in text:
            self.flush()

    def flush(self):
        text = self.buffer.getvalue()
        if text:
            self.queue.put(text)
            self.buffer = StringIO()

def capture_output(queue, upload_path):
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    output_capture = OutputCapture(queue)
    sys.stdout = output_capture
    sys.stderr = output_capture

    try:
        # Create application context for database access
        with app.app_context():
            # Set OpenAI API key from database
            api_key = get_api_key()
            if not api_key:
                queue.put("Error: OpenAI API key not configured")
                return

            os.environ['OPENAI_API_KEY'] = api_key
            os.environ['DATA_PATH'] = upload_path
            
            queue.put("Initializing Enhancement process...\n")
            enhancement = Enhancement()
            
            queue.put("Generating improvement ideas...\n")
            enhancement.ideas, enhancement.usage = enhancement.generate_improvement_ideas()
            
            # Format the output
            output = "\nIDEAS FOR CODEBASE ENHANCEMENT:\n\n"
            for index, idea in enumerate(enhancement.ideas):
                output += f"{index+1}: {idea}\n\n"
            output += f"\nAPI Usage:\n{enhancement.usage}"
            
            queue.put(output)

    except Exception as e:
        error_msg = f"Error: {str(e)}\n"
        error_msg += f"Traceback:\n{traceback.format_exc()}\n"
        queue.put(error_msg)
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        output_capture.flush()

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

@app.route('/upload-codebase', methods=['POST'])
@login_required
def upload_codebase():
    if 'codebase' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['codebase']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        # Create a unique temporary directory for this upload
        temp_dir = tempfile.mkdtemp(dir=UPLOAD_FOLDER)
        filename = secure_filename(file.filename)
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)

        # If it's a zip file, extract it
        if filename.endswith('.zip'):
            extract_dir = os.path.join(temp_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            upload_path = extract_dir
        else:
            upload_path = temp_dir

        # Store the upload path in the session for cleanup later
        session['upload_path'] = upload_path
        return jsonify({'message': 'File uploaded successfully'}), 200

    except Exception as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return jsonify({'error': str(e)}), 500

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
    # Show first 10 digits of API key if it exists
    masked_key = f"{api_key[:10]}..." if api_key else None
    return render_template('api_key.html', api_key=masked_key)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    if request.method == 'POST':
        username = request.form.get('username')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        # Verify current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect')
            return redirect(url_for('user_settings'))
        
        # Update username if provided and different
        if username and username != current_user.username:
            # Check if username is already taken
            if User.query.filter_by(username=username).first():
                flash('Username already exists')
                return redirect(url_for('user_settings'))
            current_user.username = username
        
        # Update password if provided
        if new_password:
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('Settings updated successfully')
        return redirect(url_for('dashboard'))
    
    return render_template('settings.html', user=current_user)

@app.route('/run-enhancement')
@login_required
def run_enhancement():
    upload_path = session.get('upload_path')
    if not upload_path:
        return Response("data: Error: No uploaded files found\n\n", mimetype='text/event-stream')

    def generate():
        output_queue = queue.Queue()
        thread = Thread(target=capture_output, args=(output_queue, upload_path))
        thread.start()
        
        try:
            while True:
                try:
                    output = output_queue.get(timeout=1)
                    if not output.endswith('\n'):
                        output += '\n'
                    yield f"data: {output}\n\n"
                except queue.Empty:
                    if not thread.is_alive():
                        break
                    yield "data: Processing...\n\n"
        finally:
            # Only clean up after the enhancement process is complete
            if os.path.exists(upload_path):
                parent_dir = os.path.dirname(upload_path)
                if parent_dir.startswith(UPLOAD_FOLDER):
                    shutil.rmtree(parent_dir)
            session.pop('upload_path', None)
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def init_db():
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

# Initialize database when the module is imported
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
