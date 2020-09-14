# pylint: disable=too-many-ancestors,wrong-import-position

import unittest

from django.conf import settings

if 'tcms.bugs.apps.AppConfig' not in settings.INSTALLED_APPS:
    raise unittest.SkipTest('tcms.bugs is disabled')

from django.urls import reverse                         # noqa: E402
from django.utils.translation import gettext_lazy as _  # noqa: E402

from tcms.core.helpers.comments import get_comments                   # noqa: E402
from tcms.core.templatetags.extra_filters import markdown2html        # noqa: E402
from tcms.bugs.models import Bug                                      # noqa: E402
from tcms.bugs.tests.factory import BugFactory                        # noqa: E402
from tcms.management.models import Product                            # noqa: E402
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
        user_should_have_perm(cls.tester, 'bugs.view_bug')

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


class TestEditBug(LoggedInTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        user_should_have_perm(cls.tester, 'bugs.change_bug')
        user_should_have_perm(cls.tester, 'bugs.view_bug')

    def setUp(self):
        super().setUp()
        self.bug = BugFactory()
        self.created_at = self.bug.created_at
        self.url = reverse('bugs-edit', args=(self.bug.pk,))

    def test_edit_bug(self):
        summary_edit = 'An edited summary'
        version_edit = VersionFactory()
        build_edit = BuildFactory()

        edit_data = {
            'summary': summary_edit,
            'version': version_edit.pk,
            'build': build_edit.pk,
            'reporter': self.bug.reporter.pk,
            'assignee': self.bug.assignee.pk,
            'product': self.bug.product.pk
        }

        response = self.client.post(self.url, edit_data, follow=True)

        self.assertRedirects(
            response,
            reverse('bugs-get', args=(self.bug.pk,)),
            status_code=302,
            target_status_code=200
        )

        self.bug.refresh_from_db()
        self.assertEqual(self.bug.summary, summary_edit)
        self.assertEqual(self.bug.version, version_edit)
        self.assertEqual(self.bug.build, build_edit)
        self.assertEqual(self.bug.created_at, self.created_at)

    def test_record_changes(self):
        old_summary = self.bug.summary
        new_summary = 'An edited summary'
        old_comment_count = get_comments(self.bug).count()

        edit_data = {
            'summary': new_summary,
            'version': self.bug.version.pk,
            'build': self.bug.build.pk,
            'reporter': self.bug.reporter.pk,
            'assignee': self.bug.assignee.pk,
            'product': self.bug.product.pk
        }

        self.client.post(self.url, edit_data, follow=True)
        self.bug.refresh_from_db()
        comments = get_comments(self.bug)

        self.assertEqual(comments.count(), old_comment_count + 1)
        self.assertEqual(
            comments.last().comment,
            "Summary: %s -> %s\n" % (old_summary, new_summary)
        )


class TestAddComment(LoggedInTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        user_should_have_perm(cls.tester, 'django_comments.add_comment')
        user_should_have_perm(cls.tester, 'bugs.view_bug')

        cls.bug = BugFactory()
        cls.url = reverse('bugs-comment')

    def test_add_close_bug_comment(self):
        old_comment_count = get_comments(self.bug).count()

        self.client.post(
            self.url,
            {'bug': self.bug.pk, 'text': '', 'action': 'close'},
            follow=True
        )
        comments = get_comments(self.bug)

        self.assertEqual(comments.count(), old_comment_count + 1)
        self.assertEqual(comments.last().comment, _('*bug closed*'))

    def test_add_reopen_bug_comment(self):
        old_comment_count = get_comments(self.bug).count()

        self.client.post(
            self.url,
            {'bug': self.bug.pk, 'text': '', 'action': 'reopen'},
            follow=True
        )
        comments = get_comments(self.bug)

        self.assertEqual(comments.count(), old_comment_count + 1)
        self.assertEqual(comments.last().comment, _('*bug reopened*'))


class TestSearch(LoggedInTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        user_should_have_perm(cls.tester, 'bugs.view_bug')

        ProductFactory()
        VersionFactory()
        BuildFactory()

    def test_initial_form_field_states(self):
        product_count = Product.objects.count()

        response = self.client.get(reverse('bugs-search'))
        fields = response.context['form'].fields

        self.assertEqual(fields['product'].queryset.count(), product_count)
        self.assertEqual(fields['version'].queryset.count(), 0)
        self.assertEqual(fields['build'].queryset.count(), 0)
