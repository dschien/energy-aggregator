from urllib.parse import urlparse
import os
import logging

__author__ = 'mitchell'

logger = logging.getLogger(__name__)
logger.info('Including dev-local.py configuration')

if 'DOCKER_HOST' in os.environ:
    docker_vm_ip = urlparse(os.environ.get('DOCKER_HOST')).hostname
else:
    logger.error('DOCKER_HOST is not defined')

# in local dev mode we don't care
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
DEBUG = False
ALLOWED_HOSTS.append('192.168.99.100')
ALLOWED_HOSTS.append(docker_vm_ip)

# define the hostname of the common-services
MEMCACHE_HOST = docker_vm_ip
CELERY_RESULT_BACKEND = 'cache+memcached://{}:11211/'.format(MEMCACHE_HOST)
INFLUXDB_HOST = docker_vm_ip
DB_HOST = docker_vm_ip
IODICUS_MESSAGING_HOST = docker_vm_ip
