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
        'NAME': os.environ.get('NITRATE_DB_NAME', 'nitrate'),
        'USER': os.environ.get('NITRATE_DB_USER', 'nitrate'),
        'PASSWORD': os.environ.get('NITRATE_DB_PASSWORD', 'nitrate'),
        'HOST': os.environ.get('NITRATE_DB_HOST', ''),
        'PORT': os.environ.get('NITRATE_DB_PORT', ''),
    },
    'slave_1': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('NITRATE_DB_NAME', 'nitrate'),
        'USER': os.environ.get('NITRATE_DB_USER', 'nitrate'),
        'PASSWORD': os.environ.get('NITRATE_DB_PASSWORD', 'nitrate'),
        'HOST': os.environ.get('NITRATE_DB_HOST', ''),
        'PORT': os.environ.get('NITRATE_DB_PORT', ''),
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
USER_GUIDE_URL = "http://nitrate-mrsenko.readthedocs.io/en/latest/tutorial.html"

# You can add a help link on the footer of home page as following format:
# ('http://foo.com', 'foo')
FOOTER_LINKS = (
 ('https://github.com/MrSenko/Nitrate/issues/new', 'Report an Issue'),
 (USER_GUIDE_URL, 'User guide'),
 ('http://nitrate-mrsenko.readthedocs.io/en/latest/guide/admin.html', 'Administration guide'),
 ('/xmlrpc/', 'XML-RPC service'),
)

# added for nitrate3.4 compatibility
DEFAULT_GROUPS = ['default']
TESTOPIA_XML_VERSION = '1.0'

# admin settings
ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)


DEFAULT_PAGE_SIZE = 100
