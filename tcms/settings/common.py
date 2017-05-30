# -*- coding: utf-8 -*-

import django.conf.global_settings as DEFAULT_SETTINGS
import os.path
import tcms

KIWI_VERSION = tcms.__version__

DEBUG = True

#todo: change this
# Administrators error report email settings
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

TCMS_ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..').replace('\\', '/'))

MANAGERS = ADMINS

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
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Asia/Shanghai'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# URL prefix for admin absolute URL
ADMIN_PREFIX = '/admin'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = '/usr/share/kiwi/static/'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(TCMS_ROOT_PATH, 'static').replace('\\', '/'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '^8y!)$0t7yq2+65%&_#@i^_o)eb3^q--y_$e7a_=t$%$1i)zuv'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(TCMS_ROOT_PATH, 'templates/').replace('\\', '/'),
        ],
        'OPTIONS': {
            'context_processors': DEFAULT_SETTINGS.TEMPLATE_CONTEXT_PROCESSORS + (
                'django.template.context_processors.request',
                'tcms.core.context_processors.admin_prefix_processor',
                'tcms.core.context_processors.auth_backend_processor',
                'tcms.core.context_processors.request_contents_processor',
                'tcms.core.context_processors.settings_processor',
            ),
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ]
        },
    },
]

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'tcms.core.middleware.CsrfDisableMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'pagination.middleware.PaginationMiddleware',
    # enable for kerberos authentication
    # 'django.contrib.auth.middleware.RemoteUserMiddleware',
)

ROOT_URLCONF = 'tcms.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'tcms.wsgi.application'


INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    'django_comments',
    'kobo.django.xmlrpc',

    'djcelery',
    'kombu.transport.django',
    'pagination',
    'tinymce',

    'tcms.core',
    'tcms.core.contrib.auth.apps.AppConfig',
    'tcms.core.contrib.comments.apps.AppConfig',
    'tcms.core.contrib.linkreference',
    'tcms.core.logs',
    'tcms.integration.djqpid',
    'tcms.integration.errata',
    'tcms.management',
    'tcms.profiles',
    'tcms.testcases',
    'tcms.testplans',
    'tcms.testruns',

    'tcms.xmlrpc.apps.AppConfig',
)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'


#
# Default apps settings
#

# Define the custom comment app
# http://docs.djangoproject.com/en/dev/ref/contrib/comments/custom/

COMMENTS_APP = 'tcms.core.contrib.comments'

#
# XML-RPC interface settings
#
# XML-RPC methods

XMLRPC_METHODS = {
    'TCMS_XML_RPC': (
        ('tcms.xmlrpc.api.auth', 'Auth'),
        ('tcms.xmlrpc.api.build', 'Build'),
        ('tcms.xmlrpc.api.env', 'Env'),
        ('tcms.xmlrpc.api.product', 'Product'),
        ('tcms.xmlrpc.api.testcase', 'TestCase'),
        ('tcms.xmlrpc.api.testcaserun', 'TestCaseRun'),
        ('tcms.xmlrpc.api.testcaseplan', 'TestCasePlan'),
        ('tcms.xmlrpc.api.testopia', 'Testopia'),
        ('tcms.xmlrpc.api.testplan', 'TestPlan'),
        ('tcms.xmlrpc.api.testrun', 'TestRun'),
        ('tcms.xmlrpc.api.user', 'User'),
        ('tcms.xmlrpc.api.version', 'Version'),
        ('tcms.xmlrpc.api.tag', 'Tag'),
    ),
}

XMLRPC_TEMPLATE = 'xmlrpc.html'

# Cache backend
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# Needed by django.template.context_processors.debug:
# See http://docs.djangoproject.com/en/dev/ref/templates/api/#django-template-context-processors-debug
INTERNAL_IPS = ('127.0.0.1', )

# Authentication backends
# For the login/register/logout reaon, we only support the internal auth backends.
AUTHENTICATION_BACKENDS = (
    'tcms.core.contrib.auth.backends.DBModelBackend',
    # enable for Kerberos authentication
    # 'tcms.core.contrib.auth.backends.ModAuthKerbBackend',
)

#
# Mail settings - TODO: CHANGE THESE
#
# Set the default send mail address
# See http://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_HOST = ''
EMAIL_PORT = 25
EMAIL_FROM = 'kiwi@example.com'
EMAIL_SUBJECT_PREFIX = '[Kiwi-TCMS] '
EMAILS_FOR_DEBUG = []

BROKER_URL = 'django://'
ENABLE_ASYNC_EMAIL = True

# Celery worker settings
CELERY_TASK_RESULT_EXPIRES = 60 * 2
CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'
CELERYD_TIMER_PRECISION = 120
CELERY_IGNORE_RESULT = True
CELERY_MAX_CACHED_RESULTS = -1
CELERY_DEFAULT_RATE_LIMIT = '250/m'

# TCMS email behavior settings
PLAN_EMAIL_TEMPLATE = 'mail/change_plan.txt'
PLAN_DELELE_EMAIL_TEMPLATE = 'mail/delete_plan.txt'
CASE_EMAIL_TEMPLATE = 'mail/edit_case.txt'
CASE_DELETE_EMAIL_TEMPLATE = 'mail/delete_case.txt'

# Celery async queue
import djcelery
djcelery.setup_loader()

# Maximum upload file size, default set to 5MB.
# 2.5MB - 2621440
# 5MB - 5242880
# 10MB - 10485760
# 20MB - 20971520
# 50MB - 5242880
# 100MB 104857600
# 250MB - 214958080
# 500MB - 429916160
MAX_UPLOAD_SIZE = 5242880

# Pagination
PLAN_RUNS_PAGE_SIZE = 20

# Site-specific messages

# The site can supply optional "message of the day" style banners, similar to
# /etc/motd. They are fragments of HTML.

# This if set, is shown on the login/registration screens.
MOTD_LOGIN = """<em>If it is not in KiwiTestPad, then we don't test it!</em>"""

# You can add a help link on the footer of home page as following format:
# ('http://foo.com', 'foo')
FOOTER_LINKS = (
 ('https://github.com/MrSenko/Kiwi/issues/new', 'Report an Issue'),
 (USER_GUIDE_URL, 'User guide'),
 ('http://kiwitestpad.readthedocs.io/en/latest/guide/admin.html', 'Administration guide'),
 ('/xmlrpc/', 'XML-RPC service'),
)


# Attachement file download path
# it could be spcified to a different out of MEDIA_URL
# FILE_UPLOAD_DIR = path.join(MEDIA_DIR, 'uploads').replace('\\','/'),
FILE_UPLOAD_DIR = '/var/kiwi/uploads'

# Enable the administrator delete permission
# In another word it's set the admin to super user or not.
SET_ADMIN_AS_SUPERUSER = False

# Used to construct absolute URls when interfacing with
# external systems. Must override in product.py
KIWI_BASE_URL='http://127.0.0.1:8000'

# Turn on/off listening signals sent by models.
LISTENING_MODEL_SIGNAL = True

# Kerberos settings
# Required by kerberos authentication backend
KRB5_REALM = 'EXAMPLE.COM'

# Integration with Errata system, used to linkify the Errata ID
# A valid Errata URL:
# https://errata.devel.example.com/errata/stateview/{Errata ID}
ERRATA_URL_PREFIX = ''

# user guide URL
USER_GUIDE_URL = "http://kiwitestpad.readthedocs.io/en/latest/tutorial.html"

# Default page size when paginating queries
DEFAULT_PAGE_SIZE = 100

# Disable TCMS to produce test run progress info to consumers by qpid for
# reducing unnecessary I/O access and errata does not subscribe tcms msg now.
# If you want to continue sending msg to qpid, please overwrite it in product
# .py and make sure qpid config is correct.
ENABLE_QPID = False

# TCMS use Piwik to track request.
ENABLE_PIWIK_TRACKING = False
# Piwik site id, generate by eng-ops
PIWIK_SITE_ID = ''
# Piwik api url without schema.
PIWIK_SITE_API_URL = ''
# Piwik js lib url without schema
PIWIK_SITE_JS_URL = ''

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(message)s'
        },
        'xmlrpc_log': {
            'format': '[%(asctime)s] %(levelname)s XMLRPC %(process)d "%(message)s"'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'xmlrpc': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'xmlrpc_log',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'kiwi.xmlrpc': {
            'handlers': ['xmlrpc'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

TINYMCE_DEFAULT_CONFIG = {
    'mode': "exact",
    'theme': "advanced",
    'language': "en",
    'skin': "o2k7",
    'browsers': "gecko",
    'dialog_type': "modal",
    'object_resizing': 'true',
    'cleanup_on_startup': 'true',
    'forced_root_block': "p",
    'remove_trailing_nbsp': 'true',
    'theme_advanced_toolbar_location': "top",
    'theme_advanced_toolbar_align': "left",
    'theme_advanced_statusbar_location': "none",
    'theme_advanced_buttons1': "formatselect,"
                               "bold,italic,"
                               "underline,"
                               "bullist,"
                               "numlist,"
                               "link,"
                               "unlink,"
                               "image,"
                               "search,"
                               "|,"
                               "outdent,"
                               "indent,"
                               "hr,"
                               "fullscreen,"
                               "|,"
                               "help",
    'theme_advanced_buttons2': "tablecontrols",
    'theme_advanced_buttons3': "",
    'theme_advanced_path': 'false',
    'theme_advanced_blockformats': "p,h2,h3,h4,div,code,pre",
    'theme_advanced_styles': "[all] clearfix=clearfix;"
                             "[p] summary=summary;"
                             "[div] code=code;"
                             "[img] img_left=img_left;"
                             "[img] img_left_nospacetop=img_left_nospacetop;"
                             "[img] img_right=img_right;"
                             "[img] img_right_nospacetop=img_right_nospacetop;"
                             "[img] img_block=img_block;"
                             "[img] img_block_nospacetop=img_block_nospacetop;"
                             "[div] column span-2=column span-2;"
                             "[div] column span-4=column span-4;"
                             "[div] column span-8=column span-8",
    'height': '300',
    'width': '100%',
    'urlconverter_callback': 'myCustomURLConverter',
    'plugins': "table,safari,"
               "advimage,"
               "advlink,"
               "fullscreen,"
               "visualchars,"
               "paste,"
               "media,"
               "template,"
               "searchreplace,"
               "emotions,",
    'table_styles': "Header 1=header1;"
                    "Header 2=header2;"
                    "Header 3=header3",
    'table_cell_styles': "Header 1=header1;"
                         "Header 2=header2;"
                         "Header 3=header3;"
                         "Table Cell=tableCel1",
    'table_row_styles': "Header 1=header1;"
                        "Header 2=header2;"
                        "Header 3=header3;"
                        "Table Row=tableRow1",
}

LOCALE_PATHS = (
    os.path.join(TCMS_ROOT_PATH, 'locale'),
)

TESTOPIA_XML_VERSION = '1.1'

# default group in which new users will be created
DEFAULT_GROUPS = ['default']
