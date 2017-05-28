# Django settings for devel env.

from product import *

# Debug settings
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/kiwi.devel.sqlite',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# django-debug-toolbar settings
MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

INSTALLED_APPS += (
    'debug_toolbar',
)

# For local development
ENABLE_ASYNC_EMAIL = False

FILE_UPLOAD_DIR = os.path.join(TCMS_ROOT_PATH, '..', 'uploads')
