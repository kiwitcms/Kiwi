# -*- coding: utf-8 -*-

from mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.core import mail

from tcms.core.contrib.auth.models import UserActivateKey


class TestLogout(TestCase):
    """Test for logout view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestLogout, cls).setUpTestData()

        cls.tester = User.objects.create_user(username='authtester',
                                              email='authtester@example.com',
                                              password='password')
        cls.logout_url = reverse('tcms.core.contrib.auth.views.logout')

    def test_logout_then_redirect_to_next(self):
        self.client.login(username=self.tester.username, password='password')
        response = self.client.get(self.logout_url, follow=True)
        self.assertRedirects(response, reverse('django.contrib.auth.views.login'))

    def test_logout_then_goto_next(self):
        self.client.login(username=self.tester.username, password='password')
        next_url = reverse('tcms.testplans.views.all')
        response = self.client.get(self.logout_url, {'next': next_url}, follow=True)
        self.assertRedirects(response, next_url)


class MockThread(object):
    """Mocking threading.Thread that does not run target in thread"""

    def __init__(self, target, args=None, kwargs=None):
        self.target = target
        self.args = args or ()
        self.kwargs = kwargs or {}

    def setDaemon(self, is_daemon):
        """Do nothing for setting daemon"""

    def start(self):
        self.target(*self.args, **self.kwargs)


class TestRegistration(TestCase):

    def setUp(self):
        self.register_url = reverse('tcms.core.contrib.auth.views.register')
        self.fake_activate_key = 'secret-activate-key'

    def test_open_registration_page(self):
        response = self.client.get(self.register_url)
        self.assertContains(
            response,
            '<input value="Register" class="loginbutton sprites" type="submit">',
            html=True)

    @patch('tcms.core.contrib.auth.views.settings.ENABLE_ASYNC_EMAIL', new=False)
    @patch('tcms.core.utils.mailto.threading.Thread', new=MockThread)
    @patch('hashlib.sha1')
    def assert_user_registration(self, username, sha1):
        sha1.return_value.hexdigest.return_value = self.fake_activate_key

        response = self.client.post(self.register_url,
                                    {'username': username,
                                     'password1': 'password',
                                     'password2': 'password',
                                     'email': 'new-tester@example.com'})
        self.assertContains(
            response,
            '<a href="{}">Continue</a>'.format(reverse('tcms.core.views.index')),
            html=True)

        users = User.objects.filter(username=username)
        self.assertTrue(users.exists())

        user = users[0]
        self.assertEqual('new-tester@example.com', user.email)
        self.assertFalse(user.is_active)

        keys = UserActivateKey.objects.filter(user=user)
        self.assertTrue(keys.exists())
        self.assertEqual(self.fake_activate_key, keys[0].activation_key)

        return response

    @patch('tcms.core.contrib.auth.views.settings.EMAIL_HOST', new='smtp.example.com')
    def test_register_user_by_email_confirmation(self):
        response = self.assert_user_registration('new-tester')

        self.assertContains(
            response,
            'Your accounts has been create, please check your mailbox for active')

        # Verify notification mail
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(settings.EMAIL_FROM, mail.outbox[0].from_email)
        self.assertIn(reverse('tcms.core.contrib.auth.views.confirm',
                              args=[self.fake_activate_key]),
                      mail.outbox[0].body)

    @patch('tcms.core.contrib.auth.views.settings.EMAIL_HOST', new='')
    @patch('tcms.core.contrib.auth.views.settings.ADMINS',
           new=[('admin1', 'admin1@example.com'),
                ('admin2', 'admin2@example.com')])
    def test_register_user_and_activate_by_admin(self):
        response = self.assert_user_registration('plan-tester')

        self.assertContains(
            response,
            'Your accounts has been create, but you need to contact admins '
            'to active your account')

        self.assertContains(
            response,
            '<ul><li><a href="mailto:{}">{}</a></li>'
            '<li><a href="mailto:{}">{}</a></li></ul>'.format(
                'admin1@example.com', 'admin1',
                'admin2@example.com', 'admin2'),
            html=True)


class TestConfirm(TestCase):
    """Test for activation key confirmation"""

    @classmethod
    def setUpTestData(cls):
        cls.new_user = User.objects.create(username='new-user',
                                           email='new-user@example.com',
                                           password='password')

    def test_fail_if_activation_key_not_exist(self):
        confirm_url = reverse('tcms.core.contrib.auth.views.confirm',
                              args=['nonexisting-activation-key'])
        response = self.client.get(confirm_url)

        self.assertContains(
            response,
            'They key is no longer exist in database')

        self.assertContains(
            response,
            '<a href="{}">Continue</a>'.format(reverse('tcms.core.views.index')),
            html=True)

    def test_confirm(self):
        fake_activate_key = 'secret-activate-key'

        with patch('hashlib.sha1') as sha1:
            sha1.return_value.hexdigest.return_value = fake_activate_key
            UserActivateKey.set_random_key_for_user(self.new_user)

        confirm_url = reverse('tcms.core.contrib.auth.views.confirm',
                              args=[fake_activate_key])
        response = self.client.get(confirm_url)

        self.assertContains(
            response,
            'Your accound has been activated successfully')

        self.assertContains(
            response,
            '<a href="{}">Continue</a>'.format(
                reverse('tcms.profiles.views.redirect_to_profile')),
            html=True)

        user = User.objects.get(username=self.new_user.username)
        self.assertTrue(user.is_active)
        activate_key_deleted = not UserActivateKey.objects.filter(user=user).exists()
        self.assertTrue(activate_key_deleted)
