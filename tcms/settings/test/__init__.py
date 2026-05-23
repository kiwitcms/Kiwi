# pylint: disable=wildcard-import, unused-wildcard-import, invalid-name
# pylint: disable=import-outside-toplevel,wrong-import-position, protected-access
import os
import sys
from importlib.metadata import Distribution, DistributionFinder


# pretend there are plugins (custom telemetry) installed so we can check
# the plugin loading code in settings/common.py
class FakePluginFinder(DistributionFinder):
    class FakeDistribution(Distribution):  # pylint: disable=nested-class-found
        def read_text(self, filename):
            if filename == "METADATA":
                return """Name: a_fake_plugin
Version: 0.1
"""
            if filename == "entry_points.txt":
                return """
[kiwitcms.plugins]
a_fake_plugin=tcms.telemetry.tests.plugin
"""

            return ""

        def locate_file(self, path):
            raise RuntimeError("This distribution has no file system")

    def find_distributions(self, context=DistributionFinder.Context()):
        yield self.FakeDistribution()


sys.meta_path.append(FakePluginFinder())

# this needs to be here so that  discovery tests can work
from tcms.settings.devel import *  # noqa: F401,E402,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


# for running localized tests, see f74c3c1
# See https://code.djangoproject.com/ticket/29713
LANGUAGE_CODE = os.environ.get("LANG", "en-us").lower().replace("_", "-").split(".")[0]

# Allows us to hook-up kiwitcms-django-plugin at will
TEST_RUNNER = os.environ.get("DJANGO_TEST_RUNNER", "django.test.runner.DiscoverRunner")
