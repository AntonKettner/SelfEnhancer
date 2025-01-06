#!/bin/bash

# Exit on error
set -e

echo "Starting deployment setup..."

# Create all necessary directories in Azure Web Apps storage
echo "Creating data directories..."
mkdir -p /home/site/wwwroot/data/sqlite
mkdir -p /home/site/wwwroot/data/chroma
mkdir -p /home/site/wwwroot/data/uploads
mkdir -p /home/site/wwwroot/data/temp
mkdir -p /home/site/wwwroot/data/metrics
chmod -R 755 /home/site/wwwroot/data

# Clean up any old temporary files
echo "Cleaning up old temporary files..."
find /home/site/wwwroot/data/temp -type f -mtime +1 -delete 2>/dev/null || true
find /home/site/wwwroot/data/uploads -type f -mtime +1 -delete 2>/dev/null || true

# Ensure proper permissions for streaming and metrics
echo "Setting up directory permissions..."
chmod 1777 /home/site/wwwroot/data/temp
chmod 1777 /home/site/wwwroot/data/uploads
chmod 755 /home/site/wwwroot/data/metrics

# Create SSL directory if needed
if [ -n "$WEBSITE_LOAD_CERTIFICATES" ]; then
    echo "Setting up SSL directories..."
    mkdir -p /etc/ssl/certs
    mkdir -p /etc/ssl/private
    chmod 755 /etc/ssl/certs
    chmod 700 /etc/ssl/private
fi

# Clean up old metrics files
echo "Cleaning up old metrics files..."
find /home/site/wwwroot/data/metrics -type f -mtime +7 -delete 2>/dev/null || true

echo "Directory structure:"
ls -R /home/site/wwwroot/data/

# Check database and run migrations if needed
echo "Checking database and running migrations..."
python3 << END
import os
import sys
import sqlite3
from app import create_app
from app_src.models import db
from app_src.auth import init_db
from src.migrate_api_keys import migrate_api_keys

print("Python initialization starting...")
print(f"Current working directory: {os.getcwd()}")

app = create_app()
print(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Ensure database directory exists and has correct permissions
db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
db_dir = os.path.dirname(db_path)
print(f"Database directory: {db_dir}")

if not os.path.exists(db_dir):
    print(f"Creating database directory: {db_dir}")
    os.makedirs(db_dir)
    os.chmod(db_dir, 0o755)

try:
    # Check if database needs migration
    print("Checking if migration is needed...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if user_id column exists in api_keys table
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='api_keys'")
    table_schema = cursor.fetchone()
    
    needs_migration = False
    if table_schema:
        table_sql = table_schema[0]
        if 'user_id' not in table_sql.lower():
            print("user_id column not found in api_keys table, migration needed")
            needs_migration = True
    cursor.close()
    conn.close()
    
    if needs_migration:
        print("Running API key migration...")
        with app.app_context():
            migrate_api_keys()
            print("API key migration completed successfully")
    else:
        print("No migration needed, api_keys table already has user_id column")
except Exception as e:
    print(f"Error during database check/migration: {str(e)}", file=sys.stderr)
    raise

print("Checking database file permissions:")
os.system(f"ls -l {db_path}")

END

echo "Deployment setup completed successfully"

# Final verification
echo "Final directory structure:"
ls -R /home/site/wwwroot/data/
