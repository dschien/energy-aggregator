import logging
import os

from django.conf import settings
from django.core.management import BaseCommand
import socket

__author__ = 'schien'

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test'

    def add_arguments(self, parser):
        parser.add_argument('name', default='n/a', nargs='?')

    def handle(self, *args, **options):
        logger.info('=================== Start Django configuration ===================')

        logger.info("Host name: %s" % socket.gethostname().split('.', 1)[0])
        logger.info("Container name: %s" % options['name'])
        logger.info("PROJECT ROOT: %s" % settings.PROJECT_ROOT)

        logger.info("DATABASES['default']: %s" % settings.DATABASES['default'])
        logger.info("IODICUS_MESSAGING_HOST: %s" % settings.IODICUS_MESSAGING_HOST)
        logger.info("IODICUS_MESSAGING_EXCHANGE_NAME: %s" % settings.IODICUS_MESSAGING_EXCHANGE_NAME)
        logger.info("SECURE_SERVERS: %s" % settings.SECURE_SERVERS)
        logger.info("DB_HOST: %s" % settings.DB_HOST)
        logger.info("MEMCACHE_HOST: %s" % settings.MEMCACHE_HOST)
        logger.info("INFLUXDB_HOST: %s" % settings.INFLUXDB_HOST)
        logger.info("CELERY BROKER_URL: %s" % settings.BROKER_URL)
        logger.info("CELERY_RESULT_BACKEND: %s" % settings.CELERY_RESULT_BACKEND)
        logger.info("CELERY_BROKER_HEARTBEAT: %s" % settings.BROKER_HEARTBEAT)
        logger.info("ALLOWED_HOSTS: %s" % settings.ALLOWED_HOSTS)
        logger.info("CACHES: %s" % settings.CACHES)
        # logger.info("INSTALLED_APPS: %s" % settings.INSTALLED_APPS)
        logger.info("REST_FRAMEWORK: %s" % settings.REST_FRAMEWORK)
        logger.info('=================== End Django configuration ===================')
