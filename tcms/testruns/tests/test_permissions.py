# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, too-many-ancestors


from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from tcms.tests import PermissionsTestCase, factories


class EditTestRunViewTestCase(PermissionsTestCase):
    """Test permissions for TestRun edit action"""

    permission_label = 'testruns.change_testrun'
    http_method_names = ['get', 'post']

    @classmethod
    def setUpTestData(cls):
        cls.test_run = factories.TestRunFactory(summary='Old summary')
        cls.url = reverse('testruns-edit', args=[cls.test_run.pk])
        cls.new_build = factories.BuildFactory(name='FastTest', product=cls.test_run.plan.product)
        intern = factories.UserFactory(username='intern',
                                       email='intern@example.com')
        cls.post_data = {
            'summary': 'New run summary',
            'build': cls.new_build.pk,
            'manager': cls.test_run.manager.email,
            'default_tester': intern.email,
            'notes': 'New run notes',
        }
        super().setUpTestData()

    def verify_get_with_permission(self):
        response = self.client.get(self.url)
        self.assertContains(
            response,
            '<input type="text" id="id_summary" name="summary" value="%s" class="form-control"'
            ' required>' % self.test_run.summary,
            html=True
        )
        self.assertContains(response, '<input id="id_manager" name="manager" value="%s"'
                                      ' type="text" class="form-control" placeholder='
                                      '"%s" required>'
                            % (self.test_run.manager, _('Username or email')), html=True)
        self.assertContains(response, _('Edit TestRun'))
        self.assertContains(response, 'testruns/js/mutable.js')

    def verify_post_with_permission(self):
        response = self.client.post(self.url, self.post_data)
        self.test_run.refresh_from_db()

        self.assertEqual(self.test_run.summary, 'New run summary')
        self.assertEqual(self.test_run.build, self.new_build)
        self.assertEqual(self.test_run.notes, 'New run notes')
        self.assertRedirects(
            response,
            reverse('testruns-get', args=[self.test_run.pk]))
