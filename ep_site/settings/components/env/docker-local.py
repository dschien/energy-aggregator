__author__ = 'schien'

# in local, dockerised dev mode we don't care
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
DEBUG = True
ALLOWED_HOSTS.append('192.168.99.100')
