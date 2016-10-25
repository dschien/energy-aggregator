#!/bin/bash
cd /ep_site
python manage.py migrate                  # Apply database migrations
python manage.py collectstatic --noinput  # Collect static files

python manage.py print_config $CONTAINER_NAME

# Prepare log files and start outputting logs to stdout
touch log/gunicorn.log
touch log/access.log
tail -n 0 -f log/*.log &

# Start Gunicorn processes
echo Starting Gunicorn.

exec gunicorn ep_site.wsgi:application \
    --name ep \
    --timeout 10 \
    --bind 0.0.0.0:8000 \
    --workers 5 \
    --log-level=info \
    --log-file=log/gunicorn.log \
    --access-logfile=log/access.log \
    "$@"