# import os
# PROJECT_ROOT = os.path.realpath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os

from local_settings import LOG_LEVEL

logs_folder = os.path.join(PROJECT_ROOT, 'log/')
# from pythonjsonlogger import jsonlogger
backup_count = 1
max_bytes = 1024 * 1024 * 10
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] (%(name)s) (%(funcName)s) %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'fmt': '%(levelname)s %(asctime)s %(message)s %(name)s %(funcName)s %(lineno)d %(process)d %(processName)s %(thread)d %(threadName)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        # https://docs.djangoproject.com/en/1.9/topics/logging/#django-template
        'default': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': logs_folder + 'ep_%s.log' % os.getenv('CONTAINER_NAME', ''),
            'maxBytes': max_bytes,  # 5 MB
            'backupCount': backup_count,
            'formatter': 'standard',
        },
        'celery': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': logs_folder + 'celery_%s.log' % os.getenv('CONTAINER_NAME', ''),
            'maxBytes': max_bytes,  # 5 MB
            'backupCount': backup_count,
            'formatter': 'standard',
        },
        'default-json': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': logs_folder + 'ep_%s.json' % os.getenv('CONTAINER_NAME', ''),
            'maxBytes': max_bytes,  # 5 MB
            'backupCount': backup_count,
            'formatter': 'json',
        },
        'celery-json': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': logs_folder + 'celery_%s.json' % os.getenv('CONTAINER_NAME', ''),
            'maxBytes': max_bytes,  # 5 MB
            'backupCount': backup_count,
            'formatter': 'json',
        },
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True
        },
        'null': {
            'level': LOG_LEVEL,
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'default-json', 'console'],
            'level': LOG_LEVEL,
            'propagate': True
        },
        'requests.packages.urllib3.connectionpool': {
            'handlers': ['default', 'default-json', 'console'],
            'level': 'WARN',
            'propagate': False
        },
        'django': {
            'handlers': ['default', 'default-json', 'console'],
            'level': LOG_LEVEL,
            'propagate': False
        },
        'django.template': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        # 'ep.tasks': {
        #     'handlers': ['console', 'celery', 'celery-json'],
        #     'level': LOG_LEVEL,
        #     'propagate': False
        # },
        'celery': {
            'handlers': ['console', 'celery', 'celery-json'],
            'level': LOG_LEVEL,
            'propagate': False
        },
        'django.db.backends': {
            'handlers': ['null'],  # Quiet by default!
            'propagate': False,
            'level': LOG_LEVEL,
        },

        'management_commands': {
            'handlers': ['mail_admins', 'console', 'default-json'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        # for logging
        'factory': {

            'handlers': ['default', 'console'],
            'level': 'INFO',
            'propagate': True
        },

    }
}
