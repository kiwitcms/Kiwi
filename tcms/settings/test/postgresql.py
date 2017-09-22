from tcms.settings.test import *  # noqa: F403


DATABASES['default'].update({     # noqa: F405
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'kiwi',
    'USER': 'postgres',
    'HOST': 'localhost',
})
