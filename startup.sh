#!/bin/bash

# Exit on error
set -e

echo "Starting application setup..."

# Wait for filesystem permissions to be ready
sleep 10

# Create necessary directories in Azure's persistent storage
echo "Creating data directories..."
mkdir -p /home/site/wwwroot/data/sqlite
mkdir -p /home/site/wwwroot/data/chroma
chmod -R 755 /home/site/wwwroot/data

# Set environment variables for database paths
export DATABASE_URL="sqlite:////home/site/wwwroot/data/sqlite/users.db"
export RAG_DB_PATH="/home/site/wwwroot/data/chroma"

# Initialize database and create admin user
echo "Initializing application..."
cd /home/site/wwwroot || exit 1

# Ensure scripts are executable
chmod +x deploy.sh

# Run deployment script
echo "Running deployment script..."
./deploy.sh

# Start gunicorn with the port from Azure's environment variable
echo "Starting gunicorn..."
PORT="${WEBSITES_PORT:-8000}"
exec gunicorn --bind=0.0.0.0:${PORT} --timeout 600 --access-logfile '-' --error-logfile '-' wsgi:app
