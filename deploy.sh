#!/bin/bash

# Create persistent data directory
mkdir -p /home/data

# Initialize the SQLite database
python3 << END
from app import app, db, User
with app.app_context():
    db.create_all()
    # Create admin user if it doesn't exist
    if not User.query.filter_by(username='admin').first():
        from werkzeug.security import generate_password_hash
        admin = User(username='admin', password_hash=generate_password_hash('admin'), is_admin=True)
        db.session.add(admin)
        db.session.commit()
END

# Make the script executable
chmod +x "$0"
