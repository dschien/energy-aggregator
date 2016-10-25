from local_settings import MEMCACHE_HOST
import os
from urllib.parse import urlparse

__author__ = 'schien'

# from datetime import timedelta
INSTALLED_APPS += ("djcelery",)

import djcelery

djcelery.setup_loader()

# store schedule in the DB:
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

# CELERYBEAT_SCHEDULE = {
#     'prefect-badock-every-5-minutes': {
#         'task': 'ep.tasks.import_from_site',
#         'schedule': timedelta(minutes=5),
#         'args': ('badock',),
#     },
#     'prefect-goldney-every-5-minutes': {
#         'task': 'ep.tasks.import_from_site',
#         'schedule': timedelta(minutes=5),
#         'args': ('goldney',),
#     },
#     'health_log_task': {
#         'task': 'ep.tasks.health_log_task',
#         'schedule': timedelta(minutes=5)
#     },
#     'expire-non-active-student-rooms-every-day': {
#         'task': 'heatrank.tasks.check_active_rooms',
#         'schedule': timedelta(days=1),
#     },
#
# }

CELERY_SEND_TASK_ERROR_EMAILS = True

if 'DOCKER_HOST' in os.environ:
    docker_vm_ip = urlparse(os.environ.get('DOCKER_HOST')).hostname
    RABBIT_HOST_AND_PORT = '%s:5672' % docker_vm_ip
else:
    RABBIT_HOST_AND_PORT = 'rabbit:5672'

# @todo clean up rabbit password definitions, consistent with docker-env
BROKER_URL = os.environ.get('BROKER_URL', '')
if not BROKER_URL:
    BROKER_URL = 'amqp://{user}:{password}@{hostname}/{vhost}/'.format(
        user=os.environ.get('RABBIT_ENV_USER', 'guest'),
        password=os.environ.get('RABBIT_ENV_RABBITMQ_PASS', 'guest'),
        hostname=RABBIT_HOST_AND_PORT,
        vhost=os.environ.get('RABBIT_ENV_VHOST', ''))


    #
# # We don't want to have dead connections stored on rabbitmq, so we have to negotiate using heartbeats
BROKER_HEARTBEAT_QUERY_PARAM = '?heartbeat=30'
if not BROKER_URL.endswith(BROKER_HEARTBEAT_QUERY_PARAM):
    BROKER_URL += BROKER_HEARTBEAT_QUERY_PARAM
#
BROKER_HEARTBEAT = 10

# BROKER_POOL_LIMIT = 1
# BROKER_CONNECTION_TIMEOUT = 10
#
# CELERY_DEFAULT_QUEUE = 'default'
# # CELERY_QUEUES = (
# #     Queue('default', Exchange('default'), routing_key='default'),
# # )
#
# CELERY

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_ALWAYS_EAGER = False
# CELERY_ACKS_LATE = True
# CELERY_TASK_PUBLISH_RETRY = True
# CELERY_DISABLE_RATE_LIMITS = False
# CELERY_IGNORE_RESULT = True
# CELERY_SEND_TASK_ERROR_EMAILS = False
# CELERY_RESULT_BACKEND = 'redis://%s:%d/%d' % (REDIS_HOST, REDIS_PORT, REDIS_DB)
# CELERY_RESULT_BACKEND='celery.backends.cache:CacheBackend',
CELERY_RESULT_BACKEND = 'cache+memcached://{}/'.format(MEMCACHE_HOST)
CELERY_CACHE_BACKEND_OPTIONS = {'binary': True,
                                'behaviors': {'tcp_nodelay': True}}
# CELERY_RESULT_BACKEND='djcelery.backends.cache.CacheBackend',
# CELERY_REDIS_MAX_CONNECTIONS = 1
# CELERY_TASK_RESULT_EXPIRES = 600
# CELERY_TASK_SERIALIZER = "json"
#
CELERYD_HIJACK_ROOT_LOGGER = False
# CELERYD_PREFETCH_MULTIPLIER = 1
# CELERYD_MAX_TASKS_PER_CHILD = 1000
# CELERY_ACCEPT_CONTENT = ['application/json']
