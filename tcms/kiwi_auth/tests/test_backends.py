from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, modify_settings
from guardian.utils import get_anonymous_user


@modify_settings(
    AUTHENTICATION_BACKENDS={"append": "tcms.kiwi_auth.backends.AnonymousViewBackend"}
)
class TestAnonymousViewBackend(TestCase):
    """Test AnonymousViewBackend.has_perm method"""

    def test_has_perm(self):
        user = get_anonymous_user()
        self.assertTrue(user.has_perm("testruns.view_testrun"))

    def test_not_has_perm(self):
        user = get_anonymous_user()
        self.assertFalse(user.has_perm("testruns.add_testrun"))

    def test_is_anonymous_has_perm(self):
        user = AnonymousUser()
        self.assertTrue(user.has_perm("testruns.view_testrun"))

    def test_is_anonymous_not_has_perm(self):
        user = AnonymousUser()
        self.assertFalse(user.has_perm("testruns.add_testrun"))
