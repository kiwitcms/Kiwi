from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms import tests
from tcms.bugs.models import Bug
from tcms.tests import factories


class NewTestCase(tests.PermissionsTestCase):
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
