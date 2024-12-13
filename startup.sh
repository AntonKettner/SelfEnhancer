#!/bin/bash

# Run deployment script to initialize database and create admin user
./deploy.sh

# Start gunicorn
gunicorn --bind=0.0.0.0 --timeout 600 wsgi:app
