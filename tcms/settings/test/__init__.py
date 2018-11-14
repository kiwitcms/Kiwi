# pylint: disable=wildcard-import, unused-wildcard-import

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
