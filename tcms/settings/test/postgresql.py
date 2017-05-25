from tcms.settings.test import *

DATABASES['default'].update({
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'kiwi',
    'USER': 'postgres',
    'HOST': 'localhost',
})
