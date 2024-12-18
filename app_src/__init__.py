__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from flask import Flask
from flask_login import LoginManager
from app_src.models import db, User
from app_src.config import configure_app
from app_src.auth import auth
from app_src.upload import upload
from app_src.enhancement import enhancement
from app_src.routes import main

def create_app():
    app = Flask(__name__, template_folder='../templates')
    
    # Configure app
    configure_app(app)
    
    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(auth)
    app.register_blueprint(upload)
    app.register_blueprint(enhancement)
    app.register_blueprint(main)
    
    # Initialize database
    with app.app_context():
        db.create_all()
        
        # Create admin user if it doesn't exist
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
    
    return app
