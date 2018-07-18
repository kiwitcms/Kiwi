# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, invalid-name, objects-update-used

from xmlrpc.client import Fault as XmlRPCFault

from django.contrib.auth.models import User
from django.test import TestCase

from tcms.xmlrpc.api.user import _get_user_dict

from tcms.tests.factories import GroupFactory
from tcms.tests.factories import UserFactory
from tcms.tests import user_should_have_perm
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestUserSerializer(TestCase):
    """Test User._get_user_dict"""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_ensure_password_not_returned(self):
        data = _get_user_dict(self.user)
        self.assertEqual(data['username'], self.user.username)
        self.assertEqual(data['email'], self.user.email)
        self.assertNotIn('password', data)


class TestUserFilter(XmlrpcAPIBaseTest):
    """Test User.filter"""

    def _fixture_setup(self):
        super(TestUserFilter, self)._fixture_setup()

        self.group_tester = GroupFactory()
        self.group_reviewer = GroupFactory()

        self.user1 = UserFactory(username='user 1', email='user1@exmaple.com', is_active=True,
                                 groups=[self.group_tester])
        self.user2 = UserFactory(username='user 2', email='user2@example.com', is_active=False,
                                 groups=[self.group_reviewer])
        self.user3 = UserFactory(username='user 3', email='user3@example.com', is_active=True,
                                 groups=[self.group_reviewer])

    def test_normal_search(self):
        users = self.rpc_client.exec.User.filter({'email': 'user2@example.com'})
        self.assertEqual(len(users), 1)
        user = users[0]
        self.assertEqual(user['id'], self.user2.pk)
        self.assertEqual(user['username'], self.user2.username)

        users = self.rpc_client.exec.User.filter({
            'pk__in': [self.user1.pk, self.user2.pk, self.user3.pk],
            'is_active': True
        })
        self.assertEqual(len(users), 2)

    def test_search_by_groups(self):
        users = self.rpc_client.exec.User.filter({'groups__name': self.group_reviewer.name})
        self.assertEqual(len(users), 2)

    def test_get_me(self):
        # if executed without parameters returns the current user
        data = self.rpc_client.exec.User.filter()[0]

        self.assertEqual(data['username'], self.api_user.username)
        self.assertEqual(data['id'], self.api_user.pk)
        self.assertEqual(data['first_name'], self.api_user.first_name)
        self.assertEqual(data['last_name'], self.api_user.last_name)
        self.assertEqual(data['email'], self.api_user.email)


class TestUserJoin(XmlrpcAPIBaseTest):
    """Test User.join_group"""

    def _fixture_setup(self):
        super(TestUserJoin, self)._fixture_setup()
        # needs auth.change_user
        self.api_user.is_superuser = True
        self.api_user.save()

        self.username = 'test_username'
        self.user = UserFactory(username=self.username, email='username@example.com')
        self.group_name = 'test_group'
        self.group = GroupFactory(name=self.group_name)

    def test_join_normally(self):
        self.rpc_client.exec.User.join_group(self.username, self.group_name)

        user = User.objects.get(username=self.username)
        user_added_to_group = user.groups.filter(name=self.group_name).exists()
        self.assertTrue(user_added_to_group, 'User should be added to group.')

    def test_join_nonexistent_user(self):
        with self.assertRaisesRegex(XmlRPCFault, "User matching query does not exist"):
            self.rpc_client.exec.User.join_group('nonexistent user', self.group_name)

    def test_join_nonexistent_group(self):
        with self.assertRaisesRegex(XmlRPCFault, "Group matching query does not exist"):
            self.rpc_client.exec.User.join_group(self.username, 'nonexistent group name')


class TestUserUpdate(XmlrpcAPIBaseTest):
    """Test User.update"""

    def _fixture_setup(self):
        super(TestUserUpdate, self)._fixture_setup()

        self.another_user = UserFactory()
        self.another_user.set_password('another-password')
        self.another_user.save()

        self.user_new_attrs = {
            'first_name': 'new first name',
            'last_name': 'new last name',
            'email': 'new email',
        }

    def setUp(self):
        super(TestUserUpdate, self).setUp()
        # clear permissions b/c we set them inside individual tests
        self.api_user.user_permissions.all().delete()

    def tearDown(self):
        super(TestUserUpdate, self).tearDown()
        self.api_user.set_password('api-testing')
        self.api_user.save()

    def test_update_myself(self):
        data = self.rpc_client.exec.User.update(self.api_user.pk, self.user_new_attrs)
        self.assertEqual(data['first_name'], self.user_new_attrs['first_name'])
        self.assertEqual(data['last_name'], self.user_new_attrs['last_name'])
        self.assertEqual(data['email'], self.user_new_attrs['email'])

    def test_update_myself_without_passing_id(self):
        data = self.rpc_client.exec.User.update(None, self.user_new_attrs)
        self.assertEqual(data['first_name'], self.user_new_attrs['first_name'])
        self.assertEqual(data['last_name'], self.user_new_attrs['last_name'])
        self.assertEqual(data['email'], self.user_new_attrs['email'])

    def test_update_other_missing_permission(self):
        new_values = {'some_attr': 'xxx'}
        with self.assertRaisesRegex(XmlRPCFault, "Permission denied"):
            self.rpc_client.exec.User.update(self.another_user.pk, new_values)

    def test_update_other_with_proper_permission(self):
        user_should_have_perm(self.api_user, 'auth.change_user')

        data = self.rpc_client.exec.User.update(self.another_user.pk, self.user_new_attrs)
        updated_user = User.objects.get(pk=self.another_user.pk)
        self.assertEqual(data['first_name'], updated_user.first_name)
        self.assertEqual(data['last_name'], updated_user.last_name)
        self.assertEqual(data['email'], updated_user.email)

    def test_update_own_password(self):
        user_new_attrs = self.user_new_attrs.copy()
        new_password = 'new password'
        user_new_attrs['password'] = new_password

        with self.assertRaisesRegex(XmlRPCFault, 'Old password is required'):
            self.rpc_client.exec.User.update(self.api_user.pk, user_new_attrs)

        user_new_attrs['old_password'] = 'invalid old password'
        with self.assertRaisesRegex(XmlRPCFault, "Password is incorrect"):
            self.rpc_client.exec.User.update(self.api_user.pk, user_new_attrs)

        user_new_attrs['old_password'] = 'api-testing'
        data = self.rpc_client.exec.User.update(self.api_user.pk, user_new_attrs)
        self.assertTrue('password' not in data)
        self.assertEqual(data['first_name'], user_new_attrs['first_name'])
        self.assertEqual(data['last_name'], user_new_attrs['last_name'])
        self.assertEqual(data['email'], user_new_attrs['email'])

        user = User.objects.get(pk=self.api_user.pk)
        self.assertTrue(user.check_password(new_password))

    def test_update_another_user_password(self):
        user_should_have_perm(self.api_user, 'auth.change_user')

        user_new_attrs = self.user_new_attrs.copy()
        user_new_attrs['password'] = 'new password'  # nosec:B105:hardcoded_password_string

        with self.assertRaisesRegex(XmlRPCFault,
                                    'Password updates for other users are not allowed via RPC!'):
            self.rpc_client.exec.User.update(self.another_user.pk, user_new_attrs)
