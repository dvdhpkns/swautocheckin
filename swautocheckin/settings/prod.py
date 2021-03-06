import logging
from swautocheckin.settings.common import *
import dj_database_url

DEBUG = False
INSTALLED_APPS += (
    # 'sentry',
    'raven.contrib.django.raven_compat',
)

RAVEN_CONFIG = {
    'dsn': os.environ['SENTRY_DSN'],
    # 'release': raven.fetch_git_sha(BASE_DIR),
    'CELERY_LOGLEVEL': logging.INFO,
}

SENTRY_AUTO_LOG_STACKS = True

LOGGING['handlers']['sentry'] = {
    'level': 'ERROR',
    'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
}

LOGGING['loggers'].update({
    'celery': {
        'level': 'DEBUG',
        'handlers': ['sentry', 'console'],
        'propagate': False,
    },

    'raven': {
        'level': 'DEBUG',
        'handlers': ['console'],
        'propagate': False,
    },
    'sentry.errors': {
        'level': 'DEBUG',
        'handlers': ['console'],
        'propagate': False,
    }
})

# Parse database configuration from $DATABASE_URL
DATABASES['default'] = dj_database_url.config()  # Redis config
BROKER_URL = os.environ['REDIS_URL']
CELERY_RESULT_BACKEND = os.environ['REDIS_URL']
