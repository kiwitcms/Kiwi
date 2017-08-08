# -*- coding: utf-8 -*-

import datetime

from hashlib import sha1
from mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
from django.contrib.sites.models import Site

from tcms.core.contrib.auth.models import UserActivateKey


# ### Test cases for models ###


class TestSetRandomKey(TestCase):
    """Test case for UserActivateKey.set_random_key_for_user"""

    @classmethod
    def setUpTestData(cls):
        cls.new_user = User.objects.create(username='new-tester',
                                           email='new-tester@example.com',
                                           password='password')

    @patch('tcms.core.contrib.auth.models.datetime')
    @patch('tcms.core.contrib.auth.models.random')
    def test_set_random_key(self, random, mock_datetime):
        mock_datetime.datetime.today.return_value = datetime.datetime(2017, 5, 10)
        mock_datetime.timedelta.return_value = datetime.timedelta(7)
        fake_random = 0.12345678
        random.random.return_value = fake_random

        activation_key = UserActivateKey.set_random_key_for_user(self.new_user)

        self.assertEqual(self.new_user, activation_key.user)

        s_random = sha1(str(fake_random)).hexdigest()[:5]
        expected_key = sha1('{}{}'.format(
            s_random, self.new_user.username)).hexdigest()
        self.assertEqual(expected_key, activation_key.activation_key)

        self.assertEqual(datetime.datetime(2017, 5, 17),
                         activation_key.key_expires)


class TestForceToSetRandomKey(TestCase):
    """Test case for UserActivateKey.set_random_key_for_user forcely"""

    @classmethod
    def setUpTestData(cls):
        cls.new_user = User.objects.create(username='new-tester',
                                           email='new-tester@example.com',
                                           password='password')
        cls.origin_activation_key = UserActivateKey.set_random_key_for_user(cls.new_user)

    def test_set_random_key_forcely(self):
        new_activation_key = UserActivateKey.set_random_key_for_user(self.new_user,
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

        cls.tester = User.objects.create_user(username='authtester',
                                              email='authtester@example.com',
                                              password='password')
        cls.logout_url = reverse('tcms-logout')

    def test_logout_then_redirect_to_next(self):
        self.client.login(username=self.tester.username, password='password')
        response = self.client.get(self.logout_url, follow=True)
        self.assertRedirects(response, reverse('tcms-login'))

    def test_logout_then_goto_next(self):
        self.client.login(username=self.tester.username, password='password')
        next_url = reverse('plans-all')
        response = self.client.get(self.logout_url, {'next': next_url}, follow=True)
        self.assertRedirects(response, next_url)


class TestRegistration(TestCase):

    def setUp(self):
        self.register_url = reverse('tcms-register')
        self.fake_activate_key = 'secret-activate-key'

    def test_open_registration_page(self):
        response = self.client.get(self.register_url)
        self.assertContains(
            response,
            '<input value="Register" class="loginbutton sprites" type="submit">',
            html=True)

    @patch('tcms.core.contrib.auth.models.sha1')
    def assert_user_registration(self, username, sha1):
        sha1.return_value.hexdigest.return_value = self.fake_activate_key

        response = self.client.post(self.register_url,
                                    {'username': username,
                                     'password1': 'password',
                                     'password2': 'password',
                                     'email': 'new-tester@example.com'})
        self.assertContains(
            response,
            '<a href="{}">Continue</a>'.format(reverse('core-views-index')),
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

    @patch('tcms.core.utils.mailto.send_mail')
    @patch('tcms.core.contrib.auth.views.settings.EMAIL_HOST', new='smtp.example.com')
    def test_register_user_by_email_confirmation(self, send_mail):
        response = self.assert_user_registration('new-tester')

        self.assertContains(
            response,
            'Your account has been created, please check your mailbox for confirmation')

        s = Site.objects.get_current()
        confirm_url = 'http://%s%s' % (s.domain, reverse('tcms-confirm', args=[self.fake_activate_key]))

        # Verify notification mail
        send_mail.assert_called_once_with(
            settings.EMAIL_SUBJECT_PREFIX + 'Your new 127.0.0.1:8000 account confirmation',
            """Welcome, new-tester, and thanks for signing up for an 127.0.0.1:8000 account!


%s
""" % confirm_url,
            settings.EMAIL_FROM, ['new-tester@example.com'], fail_silently=False)

    @patch('tcms.core.contrib.auth.views.settings.EMAIL_HOST', new='')
    @patch('tcms.core.contrib.auth.views.settings.ADMINS',
           new=[('admin1', 'admin1@example.com'),
                ('admin2', 'admin2@example.com')])
    def test_register_user_and_activate_by_admin(self):
        response = self.assert_user_registration('plan-tester')

        self.assertContains(
            response,
            'Your account has been created, but you need to contact an administrator '
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

    def setUp(self):
        self.new_user.is_active = False
        self.new_user.save()

    def test_fail_if_activation_key_not_exist(self):
        confirm_url = reverse('tcms-confirm',
                              args=['nonexisting-activation-key'])
        response = self.client.get(confirm_url)

        self.assertContains(
            response,
            'This key no longer exist in the database')

        self.assertContains(
            response,
            '<a href="{}">Continue</a>'.format(reverse('core-views-index')),
            html=True)

        # user account not activated
        user = User.objects.get(username=self.new_user.username)
        self.assertFalse(user.is_active)

    def test_fail_if_activation_key_expired(self):
        fake_activation_key = 'secret-activation-key'

        with patch('tcms.core.contrib.auth.models.sha1') as sha1:
            sha1.return_value.hexdigest.return_value = fake_activation_key
            key = UserActivateKey.set_random_key_for_user(self.new_user)
            key.key_expires = datetime.datetime.now() - datetime.timedelta(days=10)
            key.save()

        confirm_url = reverse('tcms-confirm', args=[fake_activation_key])
        response = self.client.get(confirm_url)

        self.assertContains(response, 'This key has expired')

        self.assertContains(
            response,
            '<a href="{}">Continue</a>'.format(reverse('core-views-index')),
            html=True)

        # user account not activated
        user = User.objects.get(username=self.new_user.username)
        self.assertFalse(user.is_active)

    def test_confirm(self):
        fake_activate_key = 'secret-activate-key'

        with patch('tcms.core.contrib.auth.models.sha1') as sha1:
            sha1.return_value.hexdigest.return_value = fake_activate_key
            UserActivateKey.set_random_key_for_user(self.new_user)

        confirm_url = reverse('tcms-confirm',
                              args=[fake_activate_key])
        response = self.client.get(confirm_url)

        self.assertContains(
            response,
            'Your account has been activated successfully')

        self.assertContains(
            response,
            '<a href="{}">Continue</a>'.format(
                reverse('tcms-redirect_to_profile')),
            html=True)

        # user account activated
        user = User.objects.get(username=self.new_user.username)
        self.assertTrue(user.is_active)
        activate_key_deleted = not UserActivateKey.objects.filter(user=user).exists()
        self.assertTrue(activate_key_deleted)
