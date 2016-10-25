__author__ = 'schien'
from ep_site.settings import *


IODICUS_MESSAGING_HOST = '{{ messaging_rabbit_host }}'

INSTALLED_APPS += ('storages',)
AWS_STORAGE_BUCKET_NAME = "ep-static"
STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

S3_URL = 'https://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
STATIC_URL = S3_URL

AWS_LOCATION = '/static'

AWS_HEADERS = {  # see http://developer.yahoo.com/performance/rules.html#expires
    'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
    'Cache-Control': 'max-age=94608000',
}