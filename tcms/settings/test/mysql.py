from tcms.settings.test import *

DATABASES['default'].update({
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'kiwi',
    'USER': 'kiwi',
    'PASSWORD': '',
    'HOST': '127.0.0.1',
    'OPTIONS': {
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    },
})
