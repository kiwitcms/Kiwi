# pylint: disable=wrong-import-position, too-many-ancestors
import unittest

from django.conf import settings

if 'tcms.bugs.apps.AppConfig' not in settings.INSTALLED_APPS:
    raise unittest.SkipTest('tcms.bugs is disabled')


from django.contrib.auth.models import Permission           # noqa: E402
from django.contrib.contenttypes.models import ContentType  # noqa: E402
from django.test import TestCase                        # noqa: E402
from django.urls import reverse                         # noqa: E402
from django.utils.translation import gettext_lazy as _  # noqa: E402

from tcms import tests            # noqa: E402
from tcms.bugs.models import Bug  # noqa: E402
from tcms.tests import factories  # noqa: E402


class TestNew(tests.PermissionsTestCase):
    permission_label = 'bugs.add_bug'
    url = reverse('bugs-new')
    http_method_names = ['get', 'post']

    @classmethod
    def setUpTestData(cls):
        version = factories.VersionFactory()
        build = factories.BuildFactory(product=version.product)

        cls.post_data = {
            'summary': 'Bug created by test suite',
            'product': version.product.pk,
            'version': version.pk,
            'build': build.pk,
        }

        super().setUpTestData()

        # cls.tester is created after calling super() above
        cls.post_data['reporter'] = cls.tester.pk

    def verify_get_with_permission(self):
        response = self.client.get(self.url)

        self.assertContains(response, _('New bug'))
        self.assertContains(response, 'bugs/js/mutable.js')

    def verify_post_with_permission(self):
        initial_count = Bug.objects.count()

        response = self.client.post(self.url, self.post_data, follow=True)

        last_bug = Bug.objects.last()
        self.assertEqual(initial_count + 1, Bug.objects.count())
        self.assertEqual(self.tester, last_bug.reporter)
        self.assertContains(response, 'Bug created by test suite')
        self.assertContains(response, 'BUG-%d' % last_bug.pk)


class TestM2MPermissionsExist(TestCase):
    def test_permissions_exist(self):
        ctype = ContentType.objects.get_for_model(Bug.tags.through)
        self.assertEqual(4, Permission.objects.filter(content_type=ctype).count())

        ctype = ContentType.objects.get_for_model(Bug.executions.through)
        self.assertEqual(4, Permission.objects.filter(content_type=ctype).count())
