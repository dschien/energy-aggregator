__author__ = 'schien'

import configparser, itertools, os
from urllib.parse import urlparse

CONFIG_FILE = "etc/docker-env"
cfg = configparser.ConfigParser()
cfg.read_file(itertools.chain(['[global]'], open(CONFIG_FILE)))
config = cfg['global']

# Make this unique, and don't share it with anybody.
SECRET_KEY = '{{ secret_key }}'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587

EMAIL_HOST_USER = '{{ gmail_user }}'
EMAIL_HOST_PASSWORD = '{{ gmail_password }}'

IODICUS_MESSAGING_EXCHANGE_NAME = '{{ exchange_name }}'
IODICUS_MESSAGING_HOST = 'rabbit'
IODICUS_MESSAGING_PORT = 5672
IODICUS_MESSAGING_USER = 'guest'
IODICUS_MESSAGING_PASSWORD = '{{ messaging_password }}'
IODICUS_MESSAGING_SSL = False

if 'TEST_SECURE_SERVER_HOST' in os.environ:
    TEST_SECURE_SERVER_HOST = urlparse(os.environ.get('TEST_SECURE_SERVER_HOST')).path
else:
    TEST_SECURE_SERVER_HOST = 'localhost'

SECURE_SERVERS = {{secure_server_dictionary}}

DB_HOST = '{{ db_host }}'
DB_PASSWORD = '{{ db_masteruserpassword }}'
DB_USER = '{{ db_master_username }}'

MEMCACHE_HOST = 'memcache:11211'

INFLUXDB_PASSWORD = config['INFLUXDB_INIT_PWD']
INFLUXDB_USER = config['ADMIN_USER']
INFLUX_DB_NAME = config['PRE_CREATE_DB']
INFLUXDB_PORT = 8086
INFLUXDB_HOST = '{{ influxdb_host }}'

LOG_LEVEL = '{{ log_level }}'

PREFECT_API_TOKEN_GOLDNEY = '{{ prefect_api_token_goldney }}'
PREFECT_API_TOKEN_BADOCK = '{{ prefect_api_token_badock }}'

RAYLEIGH_TOKEN = ''
RAYLEIGH_CLIENT_ID = ''
RAYLEIGH_APP_ID = ''

# S3 bucket name used by django 'storages' module for static files
AWS_STORAGE_BUCKET_NAME = "ep-static"

INFLUX_MEASUREMENT_SUFFIX = ''
