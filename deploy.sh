#!/bin/bash

# Exit on error
set -e

echo "Starting deployment setup..."

# Create persistent data directories in Azure Web Apps storage
echo "Creating data directories..."
mkdir -p /home/site/wwwroot/data/sqlite
mkdir -p /home/site/wwwroot/data/chroma
chmod -R 755 /home/site/wwwroot/data

# Initialize the SQLite database
echo "Initializing database..."
python3 << END
import os
import sys
from app import app, db, User
from werkzeug.security import generate_password_hash

print("Python initialization starting...")
print(f"Current working directory: {os.getcwd()}")
print(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
print(f"ChromaDB Path: {os.environ.get('RAG_DB_PATH')}")

# Ensure database directory exists
db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
db_dir = os.path.dirname(db_path)
print(f"Database directory: {db_dir}")

if not os.path.exists(db_dir):
    print(f"Creating database directory: {db_dir}")
    os.makedirs(db_dir)
    os.chmod(db_dir, 0o755)

with app.app_context():
    try:
        # Create database tables
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully")
        
        # Create admin user if it doesn't exist
        if not User.query.filter_by(username='admin').first():
            print("Creating admin user...")
            admin = User(username='admin', password_hash=generate_password_hash('admin'), is_admin=True)
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully")
        else:
            print("Admin user already exists")
    except Exception as e:
        print(f"Error during database initialization: {str(e)}", file=sys.stderr)
        raise

print("Database initialization completed successfully")
END

echo "Deployment setup completed successfully"
