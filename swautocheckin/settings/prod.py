from swautocheckin.settings.common import *
import dj_database_url

DEBUG = False
INSTALLED_APPS += (

)

# Parse database configuration from $DATABASE_URL
DATABASES['default'] = dj_database_url.config()

# Redis config
BROKER_URL = os.environ['REDISGREEN_URL'],
CELERY_RESULT_BACKEND = os.environ['REDISGREEN_URL']