from app import create_app
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import request

app = create_app()

# Handle proxy headers
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


class WSGIContextMiddleware:
    """Middleware to ensure application context is available."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        with self.app.app_context():
            return self.app.wsgi_app(environ, start_response)


# Add context middleware
application = WSGIContextMiddleware(app)

if __name__ == "__main__":
    app.run()
