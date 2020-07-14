# pylint: disable=too-many-ancestors,wrong-import-position

import unittest

from django.conf import settings

if 'tcms.bugs.apps.AppConfig' not in settings.INSTALLED_APPS:
    raise unittest.SkipTest('tcms.bugs is disabled')

from django.urls import reverse                         # noqa: E402
from django.utils.translation import gettext_lazy as _  # noqa: E402

from tcms.core.templatetags.extra_filters import markdown2html        # noqa: E402
from tcms.bugs.models import Bug                                      # noqa: E402
from tcms.bugs.tests.factory import BugFactory                        # noqa: E402
from tcms.tests import (                                              # noqa: E402
    BaseCaseRun,
    LoggedInTestCase,
    user_should_have_perm
)
from tcms.tests.factories import (                                    # noqa: E402
    BuildFactory,
    ComponentFactory,
    ProductFactory,
    UserFactory,
    VersionFactory
)
from tcms.utils.permissions import initiate_user_with_default_setups  # noqa: E402


class TestBugStatusChange(BaseCaseRun):
    """Test the possible bug status changes.

    Cases:
    * Closing an open bug.
    * Reopening a closed bug.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        initiate_user_with_default_setups(cls.tester)
        cls.comment_bug_url = reverse('bugs-comment')
        user_should_have_perm(cls.tester, 'bugs.change_bug')

    def test_close_an_open_bug(self):
        bug = BugFactory(status=True)

        edit_bug_data = {
            'bug': bug.pk,
            'text': 'Close the bug.',
            'action': 'close'
        }

        redirect_url = reverse('bugs-get', args=[bug.pk])
        response = self.client.post(self.comment_bug_url, edit_bug_data, follow=True)

        self.assertContains(response, markdown2html(_('*bug closed*')))
        self.assertContains(response, 'Close the bug.')
        self.assertRedirects(response, redirect_url)
        bug.refresh_from_db()
        self.assertFalse(bug.status)

    # test case for https://github.com/kiwitcms/Kiwi/issues/1152
    def test_reopen_a_closed_bug(self):
        bug = BugFactory(status=False)

        edit_bug_data = {
            'bug': bug.pk,
            'text': 'Reopen the bug.',
            'action': 'reopen'
        }

        redirect_url = reverse('bugs-get', args=[bug.pk])
        response = self.client.post(self.comment_bug_url, edit_bug_data, follow=True)

        self.assertContains(response, markdown2html(_('*bug reopened*')))
        self.assertContains(response, 'Reopen the bug.')
        self.assertRedirects(response, redirect_url)
        bug.refresh_from_db()
        self.assertTrue(bug.status)


class TestNewBug(LoggedInTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        user_should_have_perm(cls.tester, 'bugs.add_bug')

        cls.url = reverse('bugs-new')

        cls.summary = 'A shiny new bug!'
        cls.product = ProductFactory()
        cls.version = VersionFactory(product=cls.product)
        cls.build = BuildFactory(product=cls.product)
        cls.post_data = {
            'summary': cls.summary,
            'reporter': cls.tester.pk,
            'product': cls.product.pk,
            'version': cls.version.pk,
            'build': cls.version.pk,
        }

    def test_get_view(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_title'], _('New bug'))
        self.assertEqual(response.context['form_post_url'], reverse('bugs-new'))
        self.assertTemplateUsed(response, 'bugs/mutable.html')

        form = response.context['form']
        self.assertEqual(form.initial['reporter'].pk, self.tester.pk)
        self.assertEqual(form.fields['version'].queryset.count(), 0)
        self.assertEqual(form.fields['build'].queryset.count(), 0)

    def test_create_new_bug(self):
        initial_bug_count = Bug.objects.count()

        response = self.client.post(self.url, self.post_data)

        bug_created = Bug.objects.last()
        self.assertRedirects(
            response,
            reverse('bugs-get', args=(bug_created.pk,)),
            status_code=302,
            target_status_code=200
        )
        self.assertEqual(Bug.objects.count(), initial_bug_count + 1)
        self.assertEqual(bug_created.summary, self.summary)

    def test_new_bug_assignee_inferred_from_components(self):
        comp = ComponentFactory(initial_owner=UserFactory(), product=self.product)

        self.client.post(self.url, self.post_data, follow=True)

        bug_created = Bug.objects.last()
        self.assertEqual(bug_created.summary, self.summary)
        self.assertEqual(bug_created.assignee, comp.initial_owner)
