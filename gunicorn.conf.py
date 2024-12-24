import os
import multiprocessing
from app import app, db, User
from werkzeug.security import generate_password_hash

# Gunicorn config
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"  # Use gevent for better async support
worker_connections = 1000
timeout = 600
keepalive = 65
graceful_timeout = 120
max_requests = 1000
max_requests_jitter = 50
accesslog = "-"
errorlog = "-"
loglevel = "info"
capture_output = True
enable_stdio_inheritance = True  # Ensures proper stdout/stderr handling
forwarded_allow_ips = "*"  # Allow forwarded requests
proxy_protocol = True  # Support proxy protocol
proxy_allow_ips = "*"  # Allow proxy from any IP

# Gevent specific settings
worker_connections = 1000


def on_starting(server):
    """Initialize the application before the server starts."""
    print("Initializing application...")

    # Create necessary directories
    data_dir = "/home/data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory: {data_dir}")

    # Initialize database
    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()

            # Create admin user if it doesn't exist
            if not User.query.filter_by(username="admin").first():
                print("Creating admin user...")
                admin = User(
                    username="admin", password_hash=generate_password_hash("admin"), is_admin=True
                )
                db.session.add(admin)
                db.session.commit()
                print("Admin user created successfully")
            else:
                print("Admin user already exists")

        except Exception as e:
            print(f"Error during initialization: {str(e)}")
            raise
