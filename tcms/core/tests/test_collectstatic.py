import tempfile

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings
from parameterized import parameterized


class TestCollectstatic(TestCase):
    """
    Test manage.py collectstatic --noinput --link

    with different versions of STATICFILES_STORAGE. See
    https://github.com/sehmaschine/django-grappelli/issues/1022
    """

    @parameterized.expand(
        [
            "django.contrib.staticfiles.storage.StaticFilesStorage",
            "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
            "tcms.tests.storage.RaiseWhenFileNotFound",
        ]
    )
    def test_collect_static(self, storage):  # pylint: disable=no-self-use
        with override_settings(
            STATICFILES_STORAGE=storage,
            STATIC_ROOT=tempfile.mkdtemp(),
            STATICFILES_DIRS=[  # pylint: disable=avoid-list-comprehension
                dir
                for dir in settings.STATICFILES_DIRS
                if not dir.endswith("node_modules")
            ],
        ):
            call_command("collectstatic", "--noinput", "--link")
