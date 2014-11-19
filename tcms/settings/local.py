from tcms.settings.devel import *

import os
# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'tcms',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'tcms',
        'PASSWORD': 'redhat',
        'HOST': '10.66.140.174',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '3306',                      # Set to empty string for default.
    }
}

FIXTURE_DIRS = (os.path.join(TCMS_ROOT_PATH, 'fixtures/').replace('\\', '/'),)
