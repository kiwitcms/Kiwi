# Django settings for devel env.

from common import *

# Debug settings
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'nitrate',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'nitrate',
        'PASSWORD': 'nitrate',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

# django-debug-toolbar settings
MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

INSTALLED_APPS += (
    'debug_toolbar',
)

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False
}

# For local development
ENABLE_ASYNC_EMAIL = False

FIXTURE_DIRS = os.path.join(TCMS_ROOT_PATH, 'fixtures')
