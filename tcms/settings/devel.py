# Django settings for devel env.

from product import *

# Debug settings
DEBUG = True

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
MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

INSTALLED_APPS += [
    'debug_toolbar',
]

FILE_UPLOAD_DIR = os.path.join(TCMS_ROOT_PATH, '..', 'uploads')

# Needed by django.template.context_processors.debug:
# See http://docs.djangoproject.com/en/dev/ref/templates/api/#django-template-context-processors-debug
INTERNAL_IPS = ('127.0.0.1', )
