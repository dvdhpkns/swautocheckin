from swautocheckin.settings.common import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

INSTALLED_APPS += (
    'debug_toolbar',  # and other apps for local development
)
