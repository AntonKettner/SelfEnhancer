#!/bin/bash

# Exit on error
set -e

echo "Starting deployment setup..."

# Create persistent data directory if it doesn't exist
if [ ! -d "/home/data" ]; then
    echo "Creating /home/data directory..."
    mkdir -p /home/data
    chmod 755 /home/data
fi

# Initialize the SQLite database
echo "Initializing database..."
python3 << END
import os
from app import app, db, User
from werkzeug.security import generate_password_hash

# Ensure database directory exists
db_dir = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

with app.app_context():
    try:
        # Create database tables
        db.create_all()
        print("Database tables created successfully")
        
        # Create admin user if it doesn't exist
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password_hash=generate_password_hash('admin'), is_admin=True)
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully")
        else:
            print("Admin user already exists")
    except Exception as e:
        print(f"Error during database initialization: {str(e)}")
        raise
END

echo "Deployment setup completed successfully"
