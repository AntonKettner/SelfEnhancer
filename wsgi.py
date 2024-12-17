from app import app, init_db

# Initialize database when starting through gunicorn
init_db()

if __name__ == "__main__":
    app.run()
