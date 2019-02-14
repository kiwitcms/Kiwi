# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

import datetime
from mock import patch

from django.urls import reverse
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils.translation import ugettext_lazy as _

from tcms import signals
from tcms.tests.factories import UserFactory
from .models import UserActivationKey


User = get_user_model()  # pylint: disable=invalid-name


class TestSetRandomKey(TestCase):
    """Test case for UserActivationKey.set_random_key_for_user"""

    @classmethod
    def setUpTestData(cls):
        cls.new_user = UserFactory()

    @patch('tcms.kiwi_auth.models.datetime')
    def test_set_random_key(self, mock_datetime):
        now = datetime.datetime.now()
        in_7_days = datetime.timedelta(7)

        mock_datetime.datetime.today.return_value = now
        mock_datetime.timedelta.return_value = in_7_days

        activation_key = UserActivationKey.set_random_key_for_user(self.new_user)
        self.assertEqual(self.new_user, activation_key.user)
        self.assertNotEqual('', activation_key.activation_key)
        self.assertEqual(now + in_7_days, activation_key.key_expires)


class TestForceToSetRandomKey(TestCase):
    """Test case for UserActivationKey.set_random_key_for_user forcely"""

    @classmethod
    def setUpTestData(cls):
        cls.new_user = UserFactory()
        cls.origin_activation_key = UserActivationKey.set_random_key_for_user(cls.new_user)

    def test_set_random_key_forcely(self):
        new_activation_key = UserActivationKey.set_random_key_for_user(self.new_user,
                                                                       force=True)
        self.assertEqual(self.origin_activation_key.user, new_activation_key.user)
        self.assertNotEqual(self.origin_activation_key.activation_key,
                            new_activation_key.activation_key)


# ### Test cases for view methods ###

class TestLogout(TestCase):
    """Test for logout view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestLogout, cls).setUpTestData()

        cls.tester = UserFactory()
        cls.tester.set_password('password')
        cls.tester.save()
        cls.logout_url = reverse('tcms-logout')

    def test_logout_redirects_to_login_page(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        response = self.client.get(self.logout_url, follow=True)
        self.assertRedirects(response, reverse('tcms-login'))

    def test_logout_then_goto_next(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        next_url = reverse('tcms-login') + '?next=' + reverse('plans-search')
        response = self.client.get(self.logout_url, {'next': next_url}, follow=True)
        self.assertRedirects(response, next_url)


class TestRegistration(TestCase):

    def setUp(self):
        self.register_url = reverse('tcms-register')
        self.fake_activate_key = 'secret-activate-key'

    def test_open_registration_page(self):
        response = self.client.get(self.register_url)
        self.assertContains(response, '>%s</button>' % _('Register'))

    def assert_user_registration(self, username, follow=False):

        with patch('tcms.kiwi_auth.models.secrets') as _secrets:
            _secrets.token_hex.return_value = self.fake_activate_key

            response = self.client.post(self.register_url,
                                        {'username': username,
                                         'password1': 'password',
                                         'password2': 'password',
                                         'email': 'new-tester@example.com'},
                                        follow=follow)

        user = User.objects.get(username=username)
        self.assertEqual('new-tester@example.com', user.email)
        self.assertFalse(user.is_active)

        key = UserActivationKey.objects.get(user=user)
        self.assertEqual(self.fake_activate_key, key.activation_key)

        return response, user

    @patch('tcms.signals.USER_REGISTERED_SIGNAL.send')
    def test_register_user_sends_signal(self, signal_mock):
        self.assert_user_registration('new-signal-tester')
        self.assertTrue(signal_mock.called)
        self.assertEqual(1, signal_mock.call_count)

    @override_settings(ADMINS=[('Test Admin', 'admin@kiwitcms.org')])
    @patch('tcms.core.utils.mailto.send_mail')
    def test_signal_handler_notifies_admins(self, send_mail):
        # connect the handler b/c it is not connected by default
        signals.USER_REGISTERED_SIGNAL.connect(signals.notify_admins)

        try:
            response, user = self.assert_user_registration('signal-handler')
            self.assertRedirects(response, reverse('core-views-index'), target_status_code=302)

            # 1 - verification mail, 2 - email to admin
            self.assertTrue(send_mail.called)
            self.assertEqual(2, send_mail.call_count)

            # verify we've actually sent the admin email
            self.assertIn(str(_('New user awaiting approval')), send_mail.call_args_list[0][0][0])
            values = {
                'username': 'signal-handler',
                'user_url': 'http://testserver/admin/auth/user/%d/change/' % user.pk,
            }
            expected = _("""Dear Administrator,
somebody just registered an account with username %(username)s at your
Kiwi TCMS instance and is awaiting your approval!

Go to %(user_url)s to activate the account!
""") % values
            self.assertEqual(expected.strip(), send_mail.call_args_list[0][0][1].strip())
            self.assertIn('admin@kiwitcms.org', send_mail.call_args_list[0][0][-1])
        finally:
            signals.USER_REGISTERED_SIGNAL.disconnect(signals.notify_admins)

    @patch('tcms.core.utils.mailto.send_mail')
    def test_register_user_by_email_confirmation(self, send_mail):
        response, user = self.assert_user_registration('new-tester', follow=True)
        self.assertContains(
            response,
            _('Your account has been created, please check your mailbox for confirmation')
        )

        site = Site.objects.get_current()
        confirm_url = 'http://%s%s' % (site.domain, reverse('tcms-confirm',
                                                            args=[self.fake_activate_key]))

        # Verify notification mail
        values = {
            'user': user.username,
            'site_domain': site.domain,
            'confirm_url': confirm_url,
        }
        expected_subject = settings.EMAIL_SUBJECT_PREFIX + \
            _('Your new %s account confirmation') % site.domain
        expected_body = _("""Welcome %(user)s,
thank you for signing up for an %(site_domain)s account!

To activate your account, click this link:
%(confirm_url)s
""") % values + "\n"
        send_mail.assert_called_once_with(expected_subject, expected_body,
                                          settings.DEFAULT_FROM_EMAIL,
                                          ['new-tester@example.com'],
                                          fail_silently=False)

    @override_settings(AUTO_APPROVE_NEW_USERS=False,
                       ADMINS=[('admin1', 'admin1@example.com'),
                               ('admin2', 'admin2@example.com')])
    def test_register_user_and_activate_by_admin(self):
        response, _user = self.assert_user_registration('plan-tester', follow=True)

        self.assertContains(
            response,
            _('Your account has been created, but you need an administrator to activate it'))

        for (name, email) in settings.ADMINS:
            self.assertContains(response,
                                '<a href="mailto:{}">{}</a>'.format(email, name),
                                html=True)


class TestConfirm(TestCase):
    """Test for activation key confirmation"""

    @classmethod
    def setUpTestData(cls):
        cls.new_user = UserFactory()

    def setUp(self):
        self.new_user.is_active = False
        self.new_user.save()

    def test_fail_if_activation_key_does_not_exist(self):
        confirm_url = reverse('tcms-confirm',
                              args=['nonexisting-activation-key'])
        response = self.client.get(confirm_url, follow=True)

        self.assertContains(
            response,
            _('This activation key no longer exists in the database'))

        # user account not activated
        user = User.objects.get(username=self.new_user.username)
        self.assertFalse(user.is_active)

    def test_fail_if_activation_key_expired(self):
        fake_activation_key = 'secret-activation-key'

        with patch('tcms.kiwi_auth.models.secrets') as _secrets:
            _secrets.token_hex.return_value = fake_activation_key
            key = UserActivationKey.set_random_key_for_user(self.new_user)
            key.key_expires = datetime.datetime.now() - datetime.timedelta(days=10)
            key.save()

        confirm_url = reverse('tcms-confirm', args=[fake_activation_key])
        response = self.client.get(confirm_url, follow=True)

        self.assertContains(response, _('This activation key has expired'))

        # user account not activated
        user = User.objects.get(username=self.new_user.username)
        self.assertFalse(user.is_active)

    def test_confirm(self):
        fake_activate_key = 'secret-activate-key'

        with patch('tcms.kiwi_auth.models.secrets') as _secrets:
            _secrets.token_hex.return_value = fake_activate_key
            UserActivationKey.set_random_key_for_user(self.new_user)

        confirm_url = reverse('tcms-confirm',
                              args=[fake_activate_key])
        response = self.client.get(confirm_url, follow=True)

        self.assertContains(
            response,
            _('Your account has been activated successfully'))

        # user account activated
        user = User.objects.get(username=self.new_user.username)
        self.assertTrue(user.is_active)
        activate_key_deleted = not UserActivationKey.objects.filter(user=user).exists()
        self.assertTrue(activate_key_deleted)
