from app import create_app

app = create_app()


def application(environ, start_response):
    """WSGI application that ensures proper context handling."""
    with app.app_context():
        return app.wsgi_app(environ, start_response)


if __name__ == "__main__":
    app.run()
