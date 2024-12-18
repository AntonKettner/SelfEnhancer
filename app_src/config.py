import os

def configure_app(app):
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
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'data', 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_api_key():
    from app_src.models import APIKey
    api_key = APIKey.query.first()
    return api_key.openai_key if api_key else None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'zip', 'py', 'txt', 'md'}
