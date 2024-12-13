#!/bin/bash

# Create necessary directories with proper permissions
mkdir -p /home/data
chmod 755 /home/data

# Initialize database and create admin user
cd /home/site/wwwroot
./deploy.sh

# Start gunicorn with the port from Azure's environment variable
PORT="${WEBSITES_PORT:-8000}"
gunicorn --bind=0.0.0.0:${PORT} --timeout 600 wsgi:app
