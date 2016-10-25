import os
from celery import Celery
from django.conf import settings

__author__ = 'schien'

# from __future__ import absolute_import

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ep_site.settings')

app = Celery('ep')

# Using a string here means the worker will not have to
# pickle the object when using Windows.

# app.config_from_object('django.conf:settings')
app.config_from_object('django.conf:settings')
# app.config_from_object('ep_site.celeryconfig')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
