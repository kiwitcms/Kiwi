# pylint: disable=too-many-ancestors
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms.tests import BaseCaseRun, user_should_have_perm
from tcms.tests.factories import BugFactory
from tcms.utils.permissions import initiate_user_with_default_setups
from tcms.core.templatetags.extra_filters import markdown2html


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
