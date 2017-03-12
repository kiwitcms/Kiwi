# -*- coding: utf-8 -*-

from httplib import FORBIDDEN
from httplib import NOT_FOUND

from django.contrib.auth.models import User
from django.test import TestCase

import tcms.xmlrpc.api.user as XUser

from tcms.xmlrpc.tests.utils import make_http_request
from tcms.xmlrpc.tests.utils import user_should_have_perm
from tcms.tests.factories import UserFactory
from tcms.tests.factories import GroupFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestUserSerializer(TestCase):
    '''Test User.get_user_dict'''

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.http_req = make_http_request(user=cls.user)

    def test_ensure_password_not_returned(self):
        data = XUser.get_user_dict(self.user)
        self.assertEqual(data['username'], self.user.username)
        self.assertEqual(data['email'], self.user.email)
        self.assertNotIn('password', data)


class TestUserFilter(TestCase):
    '''Test User.filter'''

    @classmethod
    def setUpTestData(cls):
        cls.group_tester = GroupFactory()
        cls.group_reviewer = GroupFactory()

        cls.user1 = UserFactory(username='user 1', email='user1@exmaple.com', is_active=True,
                                groups=[cls.group_tester])
        cls.user2 = UserFactory(username='user 2', email='user2@example.com', is_active=False,
                                groups=[cls.group_reviewer])
        cls.user3 = UserFactory(username='user 3', email='user3@example.com', is_active=True,
                                groups=[cls.group_reviewer])

        cls.http_req = make_http_request()

    def test_normal_search(self):
        users = XUser.filter(self.http_req, {'email': 'user2@example.com'})
        self.assertEqual(len(users), 1)
        user = users[0]
        self.assertEqual(user['id'], self.user2.pk)
        self.assertEqual(user['username'], self.user2.username)

        users = XUser.filter(self.http_req, {
            'pk__in': [self.user1.pk, self.user2.pk, self.user3.pk],
            'is_active': True
        })
        self.assertEqual(len(users), 2)

    def test_search_by_groups(self):
        users = XUser.filter(self.http_req,
                             {'groups__name': self.group_reviewer.name})
        self.assertEqual(len(users), 2)


class TestUserGet(XmlrpcAPIBaseTest):
    '''Test User.get'''

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.http_req = make_http_request(user=cls.user)

    def test_get(self):
        test_user = self.http_req.user
        data = XUser.get(self.http_req, test_user.pk)

        self.assertEqual(data['username'], test_user.username)
        self.assertEqual(data['id'], test_user.pk)
        self.assertEqual(data['first_name'], test_user.first_name)
        self.assertEqual(data['last_name'], test_user.last_name)
        self.assertEqual(data['email'], test_user.email)

    def test_get_not_exist(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, XUser.get, self.http_req, self.http_req.user.pk + 1)


class TestUserGetMe(TestCase):
    '''Test User.get_me'''

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.http_req = make_http_request(user=cls.user)

    def test_get_me(self):
        test_user = self.http_req.user
        data = XUser.get_me(self.http_req)
        self.assertEqual(data['id'], test_user.pk)
        self.assertEqual(data['username'], test_user.username)


class TestUserJoin(XmlrpcAPIBaseTest):
    '''Test User.join'''

    @classmethod
    def setUpTestData(cls):
        cls.http_req = make_http_request(user_perm='auth.change_user')
        cls.username = 'test_username'
        cls.user = UserFactory(username=cls.username, email='username@example.com')
        cls.group_name = 'test_group'
        cls.group = GroupFactory(name=cls.group_name)

    def test_join_normally(self):
        XUser.join(self.http_req, self.username, self.group_name)

        user = User.objects.get(username=self.username)
        user_added_to_group = user.groups.filter(name=self.group_name).exists()
        self.assertTrue(user_added_to_group, 'User should be added to group.')

    def test_join_nonexistent_user(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, XUser.join,
                                     self.http_req, 'nonexistent user', 'whatever group name')

    def test_join_nonexistent_group(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, XUser.join,
                                     self.http_req, self.username, 'nonexistent group name')


class TestUserUpdate(XmlrpcAPIBaseTest):
    '''Test User.update'''

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(username='bob', email='bob@example.com')
        cls.user.set_password(cls.user.username)
        cls.user.save()

        cls.another_user = UserFactory()

        cls.http_req = make_http_request(user=cls.user)
        cls.user_new_attrs = {
            'first_name': 'new first name',
            'last_name': 'new last name',
            'email': 'new email',
        }

    def test_update_myself(self):
        data = XUser.update(self.http_req,
                            self.user_new_attrs, self.http_req.user.pk)
        self.assertEqual(data['first_name'], self.user_new_attrs['first_name'])
        self.assertEqual(data['last_name'], self.user_new_attrs['last_name'])
        self.assertEqual(data['email'], self.user_new_attrs['email'])

    def test_update_myself_without_passing_id(self):
        data = XUser.update(self.http_req, self.user_new_attrs)
        self.assertEqual(data['first_name'], self.user_new_attrs['first_name'])
        self.assertEqual(data['last_name'], self.user_new_attrs['last_name'])
        self.assertEqual(data['email'], self.user_new_attrs['email'])

    def test_update_other_missing_permission(self):
        new_values = {'some_attr': 'xxx'}
        self.assertRaisesXmlrpcFault(FORBIDDEN, XUser.update,
                                     self.http_req, new_values, self.another_user.pk)

    def test_update_other_with_proper_permission(self):
        user_should_have_perm(self.http_req.user, 'auth.change_user')

        data = XUser.update(self.http_req, self.user_new_attrs, self.user.pk)
        updated_user = User.objects.get(pk=self.user.pk)
        self.assertEqual(data['first_name'], updated_user.first_name)
        self.assertEqual(data['last_name'], updated_user.last_name)
        self.assertEqual(data['email'], updated_user.email)

    def test_update_password(self):
        test_user = self.http_req.user

        # make sure user who is shooting the request has proper permission to
        # update an user's attributes, whatever itself or others.
        user_should_have_perm(test_user, 'auth.change_user')

        user_new_attrs = self.user_new_attrs.copy()
        new_password = 'new password'
        user_new_attrs['password'] = new_password

        self.assertRaisesXmlrpcFault(FORBIDDEN, XUser.update,
                                     self.http_req, user_new_attrs, test_user.pk)

        user_new_attrs['old_password'] = 'invalid old password'
        self.assertRaisesXmlrpcFault(FORBIDDEN, XUser.update,
                                     self.http_req, user_new_attrs, test_user.pk)

        user_new_attrs['old_password'] = test_user.username
        data = XUser.update(self.http_req, user_new_attrs, test_user.pk)
        self.assert_('password' not in data)
        self.assertEqual(data['first_name'], user_new_attrs['first_name'])
        self.assertEqual(data['last_name'], user_new_attrs['last_name'])
        self.assertEqual(data['email'], user_new_attrs['email'])

        user = User.objects.get(pk=test_user.pk)
        self.assert_(user.check_password(new_password))
