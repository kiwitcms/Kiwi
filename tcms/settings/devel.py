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
        "PASSWORD": "",
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

MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa: F405

INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405

MEDIA_ROOT = os.path.join(TCMS_ROOT_PATH, "..", "uploads")  # noqa: F405

# Needed by django.template.context_processors.debug:
# See:
# http://docs.djangoproject.com/en/dev/ref/templates/api/#django-template-context-processors-debug
INTERNAL_IPS = ("127.0.0.1",)

STATICFILES_STORAGE = "tcms.tests.storage.RaiseWhenFileNotFound"
