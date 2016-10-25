#!/bin/bash
python manage.py print_config $CONTAINER_NAME
celery -A ep_site beat