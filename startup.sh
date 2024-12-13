#!/bin/bash

# Create necessary directories with proper permissions
mkdir -p /home/data
chmod 755 /home/data

# Initialize database and create admin user
cd /home/site/wwwroot
./deploy.sh

# Start gunicorn
gunicorn --bind=0.0.0.0 --timeout 600 wsgi:app
