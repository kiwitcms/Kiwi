from tcms.settings.devel import *  # noqa: F401,F403

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

LISTENING_MODEL_SIGNAL = False

STATICFILES_STORAGE = 'tcms.tests.storage.RaiseWhenFileNotFound'
