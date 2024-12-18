__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from flask import Flask
import os
from app_src.models import db
from app_src.auth import auth_bp, login_manager, init_db
from app_src.routes import main_bp
from config.settings import *

def create_app():
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

    # Configure upload settings
    os.makedirs(UPLOADS_PATH, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Initialize database
    init_db(app)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
