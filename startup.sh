#!/bin/bash

# Exit on error
set -e

echo "Starting application setup..."

# Wait for filesystem permissions to be ready
sleep 10

# Create data directory in the persistent storage location
echo "Creating data directory..."
mkdir -p /home/site/wwwroot/data
chmod 755 /home/site/wwwroot/data

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
