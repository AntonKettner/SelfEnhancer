import os
import multiprocessing
from app import app, db, User
from werkzeug.security import generate_password_hash

# Gunicorn config
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"  # Use gevent for better async support
worker_connections = 1000
threads = 4  # Number of threads per worker

# Timeouts and keepalive
timeout = 600
keepalive = 65
graceful_timeout = 120

# Worker lifecycle
max_requests = 1000
max_requests_jitter = 50
preload_app = True  # Preload app to share application context

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
capture_output = True
enable_stdio_inheritance = True

# Proxy settings
forwarded_allow_ips = "*"
proxy_protocol = True
proxy_allow_ips = "*"

# SSL settings (for Azure)
ssl_version = 5  # TLS


def on_starting(server):
    """Initialize the application before the server starts."""
    print("Initializing application...")

    # Create necessary directories
    data_dir = "/home/data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory: {data_dir}")

    # Initialize database and run migrations
    from app_src.auth import init_db

    try:
        init_db(app)
    except Exception as e:
        print(f"Error during initialization: {str(e)}")
        raise
