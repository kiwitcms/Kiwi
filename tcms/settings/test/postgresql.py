# pylint: disable=wildcard-import, unused-wildcard-import, objects-update-used

from tcms.settings.test import *  # noqa: F403

DATABASES['default'].update({     # noqa: F405
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': 'kiwi',
    'USER': 'kiwi',
    'PASSWORD': 'kiwi',
    'HOST': 'localhost',
})
