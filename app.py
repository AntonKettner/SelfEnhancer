__import__("pysqlite3")
import sys

sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

from flask import Flask
import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from prometheus_flask_exporter import PrometheusMetrics
from app_src.models import db
from app_src.auth import auth_bp, login_manager, init_db
from app_src.routes import main_bp
from config.settings import *

# Initialize Sentry if DSN is provided
SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")
    if not app.config["SECRET_KEY"]:
        raise ValueError("No SECRET_KEY set for Flask application")

    # Use Azure Web App's persistent storage for SQLite database
    default_db_path = "sqlite:////home/site/wwwroot/data/sqlite/users.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", default_db_path)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["PROPAGATE_EXCEPTIONS"] = True  # Ensure exceptions are propagated

    # Ensure database directory exists
    db_dir = os.path.dirname(app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", ""))
    os.makedirs(db_dir, exist_ok=True)
    os.chmod(db_dir, 0o755)

    # Configure upload settings
    os.makedirs(UPLOADS_PATH, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Initialize Prometheus metrics if in production
    if not app.debug:
        try:
            metrics = PrometheusMetrics(app)
            metrics.info("app_info", "Application info", version="1.0.0")

            # Add custom metrics
            metrics.counter("enhancement_total", "Number of enhancement processes started")
            metrics.counter("enhancement_errors", "Number of enhancement process errors")
            metrics.histogram(
                "enhancement_duration_seconds",
                "Time spent processing enhancements",
                buckets=[30, 60, 120, 180, 240, 300, 600],
            )

            # Add OpenAI API metrics
            metrics.histogram(
                "openai_api_latency_seconds",
                "Time spent waiting for OpenAI API",
                buckets=[0.5, 1, 2, 5, 10, 30, 60],
            )
            metrics.counter("openai_api_errors", "Number of OpenAI API errors")

            print("Prometheus metrics initialized successfully")
        except Exception as e:
            print(f"Warning: Failed to initialize Prometheus metrics: {str(e)}")
            # Continue without metrics in case of initialization failure

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Initialize database and run migrations if needed
    init_db(app)

    # Run API key migration if needed
    with app.app_context():
        from src.migrate_api_keys import migrate_api_keys

        migrate_api_keys()

    @app.after_request
    def after_request(response):
        """Ensure proper headers for streaming responses."""
        if response.mimetype == "text/event-stream":
            response.headers["Cache-Control"] = "no-cache"
            response.headers["X-Accel-Buffering"] = "no"
            response.headers["Connection"] = "keep-alive"
            response.headers["X-Accel-Buffering"] = "no"
        return response

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
