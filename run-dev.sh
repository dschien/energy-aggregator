#!/bin/bash

# Collect static files
echo "Collect static files"
python manage.py collectstatic --noinput

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

# Apply groups fixtures
echo "Apply groups fixtures"
python manage.py loaddata initial_deploy.json

# Create dev-local credentials
echo "Apply dev-local credentials"
python manage.py loaddata dev-local_credentials.json

# Run the integration test to create the messaging exchange
echo "Running integration test"
python manage.py integration_test

# Start server
echo "Starting server"
python manage.py runserver 0.0.0.0:8000

# gunicorn composeexample.wsgi:application -w 2 -b :8000