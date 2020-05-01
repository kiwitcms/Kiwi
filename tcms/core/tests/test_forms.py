# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
from django.test import TestCase
from django.core.exceptions import ValidationError

from tcms.core.forms.fields import UserField
from tcms.tests.factories import UserFactory


class TestUserField(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(username='admin', email='admin@example.com')
        cls.user_field = UserField()

    def setUp(self):
        self.user_field.required = True

    def test_valid_username_accepted(self):
        form_user = self.user_field.clean("admin")
        self.assertEqual(form_user.email, self.user.email)
        self.assertEqual(form_user.username, self.user.username)

    def test_empty_username_when_required_throws_error(self):
        with self.assertRaisesRegex(ValidationError, 'A user name or user ID is required.'):
            self.user_field.clean('')

    def test_none_username_when_required_throws_error(self):
        with self.assertRaisesRegex(ValidationError, 'A user name or user ID is required.'):
            self.user_field.clean(None)

    def test_none_username_accepted_when_not_required(self):
        self.user_field.required = False
        self.assertIsNone(self.user_field.clean(None))

    def test_empty_username_accepted_when_not_required(self):
        self.user_field.required = False
        self.assertIsNone(self.user_field.clean(''))

    def test_int_instance_username_accepted(self):
        form_user = self.user_field.clean(self.user.pk)
        self.assertEqual(form_user.email, self.user.email)
        self.assertEqual(form_user.username, self.user.username)

    def test_not_existing_int_instance_username_throws_error(self):
        user_id = -1
        with self.assertRaisesRegex(ValidationError, ('Unknown user_id: "%d"' % user_id)):
            self.user_field.clean(user_id)

    def test_digit_username_accepted(self):
        form_user = self.user_field.clean(str(self.user.pk))
        self.assertEqual(form_user.email, self.user.email)
        self.assertEqual(form_user.username, self.user.username)

    def test_not_existing_digit_username_throws_error(self):
        user_id = "999999"
        with self.assertRaisesRegex(ValidationError, ('Unknown user_id: "%s"' % user_id)):
            self.user_field.clean(user_id)

    def test_not_existing_string_username_throws_error(self):
        with self.assertRaisesRegex(ValidationError, 'Unknown user: "UnknownUser"'):
            self.user_field.clean('UnknownUser')
