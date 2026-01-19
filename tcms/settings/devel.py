# pylint: disable=wildcard-import, unused-wildcard-import
"""
Django settings for devel env.
"""

import os

from .common import *  # noqa: F403

# Debug settings
DEBUG = True

# Database settings
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(TEMP_DIR / "kiwi.devel.sqlite"),  # noqa: F405
        "USER": "root",
        "PASSWORD": "",  # nosec:B105:hardcoded_password_string
        "HOST": "",
        "PORT": "",
    }
}


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}
# django-debug-toolbar settings

MIDDLEWARE += [  # noqa: F405
    "tcms.core.middleware.ExtraHeadersMiddleware",
]

MEDIA_ROOT = os.path.join(TCMS_ROOT_PATH, "..", "uploads")  # noqa: F405

# Needed by django.template.context_processors.debug:
# See:
# http://docs.djangoproject.com/en/dev/ref/templates/api/#django-template-context-processors-debug
INTERNAL_IPS = ("127.0.0.1",)

STORAGES["staticfiles"][  # noqa: F405
    "BACKEND"
] = "tcms.tests.storage.RaiseWhenFileNotFound"

ANONYMOUS_ANALYTICS = False
