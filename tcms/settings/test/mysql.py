from tcms.settings.test import *

DATABASES['default'].update({
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'nitrate',
    'USER': 'nitrate',
    'PASSWORD': '',
    'HOST': '127.0.0.1',
})
