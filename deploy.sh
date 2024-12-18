#!/bin/bash

# Exit on error
set -e

echo "Starting deployment setup..."

# Create all necessary directories in Azure Web Apps storage
echo "Creating data directories..."
mkdir -p /home/site/wwwroot/data/sqlite
mkdir -p /home/site/wwwroot/data/chroma
mkdir -p /home/site/wwwroot/data/uploads
chmod -R 755 /home/site/wwwroot/data

echo "Directory structure:"
ls -R /home/site/wwwroot/data/

# Initialize the SQLite database
echo "Initializing database..."
python3 << END
import os
import sys
from app import create_app
from app_src.models import db
from app_src.auth import init_db

print("Python initialization starting...")
print(f"Current working directory: {os.getcwd()}")

app = create_app()
print(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
print(f"ChromaDB Path: {os.environ.get('RAG_DB_PATH')}")

# Ensure database directory exists and has correct permissions
db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
db_dir = os.path.dirname(db_path)
print(f"Database directory: {db_dir}")

if not os.path.exists(db_dir):
    print(f"Creating database directory: {db_dir}")
    os.makedirs(db_dir)
    os.chmod(db_dir, 0o755)

try:
    print("Initializing database...")
    init_db(app)
    print("Database initialization completed successfully")
except Exception as e:
    print(f"Error during database initialization: {str(e)}", file=sys.stderr)
    raise

print("Checking database file permissions:")
os.system(f"ls -l {db_path}")

END

echo "Deployment setup completed successfully"

# Final verification
echo "Final directory structure:"
ls -R /home/site/wwwroot/data/
