import os
from tcms.settings.devel import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

if 'TRAVIS' in os.environ:
    if os.environ.get('TEST_DB').lower() in ['mysql', 'mariadb']:
        DATABASES['default'].update({
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'nitrate_travis',
            'USER': 'travis',
            'HOST': '127.0.0.1',
        })
    elif os.environ.get('TEST_DB').lower() == 'postgres':
        DATABASES['default'].update({
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'nitrate_travis',
            'USER': 'postgres',
            'HOST': 'localhost',
        })

LISTENING_MODEL_SIGNAL = False

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
