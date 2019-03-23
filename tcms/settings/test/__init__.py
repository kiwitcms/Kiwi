# pylint: disable=wildcard-import, unused-wildcard-import

import os
import warnings

from tcms.settings.devel import *  # noqa: F401,F403


# silence resource warnings while testing, see
# https://emptysqua.re/blog/against-resourcewarnings-in-python-3/
warnings.simplefilter("ignore", ResourceWarning)


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}


# for running localized tests, see f74c3c1
# See https://code.djangoproject.com/ticket/29713
LANGUAGE_CODE = os.environ.get('LANG', 'en-us').lower().replace('_', '-').split('.')[0]
