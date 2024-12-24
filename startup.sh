#!/bin/bash

# Exit on error
set -e

echo "Starting application setup..."

# Wait for filesystem permissions to be ready
sleep 10

# Set environment variables for database paths
export DATABASE_URL="sqlite:////home/site/wwwroot/data/sqlite/users.db"
export RAG_DB_PATH="/home/site/wwwroot/data/chroma"

# Debug information
echo "Environment Setup:"
echo "Current directory: $(pwd)"
echo "Database URL: $DATABASE_URL"
echo "RAG DB Path: $RAG_DB_PATH"

# Initialize database and create admin user
echo "Initializing application..."
cd /home/site/wwwroot || exit 1

# Ensure scripts are executable
chmod +x deploy.sh

# Run deployment script
echo "Running deployment script..."
./deploy.sh

# Start gunicorn with configuration file
echo "Starting gunicorn..."
PORT="${WEBSITES_PORT:-8000}"
export GUNICORN_CMD_ARGS="--bind=0.0.0.0:${PORT} --config=gunicorn.conf.py --preload --max-requests 1000 --max-requests-jitter 50"
exec gunicorn wsgi:application
