__author__ = 'schien'

INSTALLED_APPS += ('storages',)

STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

S3_URL = 'https://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
STATIC_URL = S3_URL

AWS_LOCATION = '/static'

AWS_HEADERS = {  # see http://developer.yahoo.com/performance/rules.html#expires
    'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
    'Cache-Control': 'max-age=94608000',
}

IODICUS_MESSAGING_EXCHANGE_NAME = 'LES_EVENTS_staging'

# ALLOWED_HOSTS.append('52.50.177.77')

INFLUX_MEASUREMENT_SUFFIX = '_staging'

