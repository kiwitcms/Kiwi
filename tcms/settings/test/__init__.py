# pylint: disable=wildcard-import, unused-wildcard-import, invalid-name

import os
import warnings
import pkg_resources

# pretend there are telemetry plugins installed so we can check
# the plugin loading code in settings/common.py
dist = pkg_resources.Distribution(__file__)
entry_point = pkg_resources.EntryPoint.parse('a_fake_plugin = tcms.telemetry.tests.plugin',
                                             dist=dist)
dist._ep_map = {'kiwitcms.telemetry.plugins': {'a_fake_plugin': entry_point}}
pkg_resources.working_set.add(dist)

# this needs to be here so that  discovery tests can work
from tcms.settings.devel import *  # noqa: F401,F403 pylint: disable=C0413,import-outside-toplevel


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
