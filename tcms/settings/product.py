# Django settings for product env.

import os
from common import *

# Debug settings
DEBUG = False
TEMPLATE_DEBUG = DEBUG

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('KIWI_DB_NAME', 'kiwi'),
        'USER': os.environ.get('KIWI_DB_USER', 'kiwi'),
        'PASSWORD': os.environ.get('KIWI_DB_PASSWORD', 'kiwi'),
        'HOST': os.environ.get('KIWI_DB_HOST', ''),
        'PORT': os.environ.get('KIWI_DB_PORT', ''),
    },
    'slave_1': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('KIWI_DB_NAME', 'kiwi'),
        'USER': os.environ.get('KIWI_DB_USER', 'kiwi'),
        'PASSWORD': os.environ.get('KIWI_DB_PASSWORD', 'kiwi'),
        'HOST': os.environ.get('KIWI_DB_HOST', ''),
        'PORT': os.environ.get('KIWI_DB_PORT', ''),
    },
}

# add RemoteUserMiddleWare if kerberos authentication is enabled
MIDDLEWARE_CLASSES += (
#    'django.contrib.auth.middleware.RemoteUserMiddleware',
)

# Remote kerberos authentication backends
#AUTHENTICATION_BACKENDS = (
#    'tcms.core.contrib.auth.backends.ModAuthKerbBackend',
#)

DATABASE_ROUTERS = ['tcms.core.utils.tcms_router.RWRouter']

# Kerberos realm
#KRB5_REALM = 'EXAMPLE.COM'

# Set the default send mail address
EMAIL_HOST = 'smtp.example.com'
EMAIL_FROM = 'noreply@example.com'

# Site-specific messages

# First run - to detemine need port user or not.
FIRST_RUN = False

# user guide URL
USER_GUIDE_URL = "http://kiwitestpad.readthedocs.io/en/latest/tutorial.html"

# You can add a help link on the footer of home page as following format:
# ('http://foo.com', 'foo')
FOOTER_LINKS = (
 ('https://github.com/MrSenko/Kiwi/issues/new', 'Report an Issue'),
 (USER_GUIDE_URL, 'User guide'),
 ('http://kiwitestpad.readthedocs.io/en/latest/guide/admin.html', 'Administration guide'),
 ('/xmlrpc/', 'XML-RPC service'),
)

DEFAULT_GROUPS = ['default']

# admin settings
ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)


DEFAULT_PAGE_SIZE = 100
