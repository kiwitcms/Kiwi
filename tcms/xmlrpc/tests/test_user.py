# -*- coding: utf-8 -*-

from xmlrpclib import Fault

from django.contrib.auth.models import User
from django.test import TestCase

import tcms.xmlrpc.api.user as XUser

from tcms.xmlrpc.tests.utils import make_http_request
from tcms.xmlrpc.tests.utils import user_should_have_perm
from tcms.tests.factories import UserFactory
from tcms.tests.factories import GroupFactory


class TestUserSerializer(TestCase):
    '''Test User.get_user_dict'''

    def setUp(self):
        self.user = UserFactory()
        self.http_req = make_http_request(user=self.user)

    def test_ensure_password_not_returned(self):
        data = XUser.get_user_dict(self.user)
        self.assertEqual(data['username'], self.user.username)
        self.assertEqual(data['email'], self.user.email)
        self.assertNotIn('password', data)


class TestUserFilter(TestCase):
    '''Test User.filter'''

    @classmethod
    def setUpClass(cls):
        cls.group_tester = GroupFactory(name='tester')
        cls.group_reviewer = GroupFactory(name='reviewer')

        cls.user1 = UserFactory(username='user 1', email='user1@exmaple.com', is_active=True,
                                groups=[cls.group_tester])
        cls.user2 = UserFactory(username='user 2', email='user2@example.com', is_active=False,
                                groups=[cls.group_reviewer])
        cls.user3 = UserFactory(username='user 3', email='user3@example.com', is_active=True,
                                groups=[cls.group_reviewer])

        cls.http_req = make_http_request()

    @classmethod
    def tearDownClass(cls):
        cls.user1.groups.clear()
        cls.user2.groups.clear()
        cls.user3.groups.clear()
        cls.group_tester.delete()
        cls.group_reviewer.delete()
        cls.user1.delete()
        cls.user2.delete()
        cls.user3.delete()

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


class TestUserGet(TestCase):
    '''Test User.get'''

    def setUp(self):
        self.http_req = make_http_request()

    def test_get(self):
        test_user = self.http_req.user
        data = XUser.get(self.http_req, test_user.pk)

        self.assertEqual(data['username'], test_user.username)
        self.assertEqual(data['id'], test_user.pk)
        self.assertEqual(data['first_name'], test_user.first_name)
        self.assertEqual(data['last_name'], test_user.last_name)
        self.assertEqual(data['email'], test_user.email)

    def test_get_not_exist(self):
        try:
            XUser.get(self.http_req, self.http_req.user.pk + 1)
        except Fault as e:
            self.assertEqual(e.faultCode, 404)


class TestUserGetMe(TestCase):
    '''Test User.get_me'''

    def setUp(self):
        self.http_req = make_http_request()

    def test_get_me(self):
        test_user = self.http_req.user
        data = XUser.get_me(self.http_req)
        self.assertEqual(data['id'], test_user.pk)
        self.assertEqual(data['username'], test_user.username)


class TestUserJoin(TestCase):
    '''Test User.join'''

    @classmethod
    def setUpClass(cls):
        cls.http_req = make_http_request(user_perm='auth.change_user')
        cls.username = 'test_username'
        cls.user = UserFactory(username=cls.username, email='username@example.com')
        cls.group_name = 'test_group'
        cls.group = GroupFactory(name=cls.group_name)

    @classmethod
    def tearDownClass(cls):
        cls.user.groups.clear()
        cls.group.delete()
        cls.user.delete()

    def test_join_normally(self):
        XUser.join(self.http_req, self.username, self.group_name)

        user = User.objects.get(username=self.username)
        user_added_to_group = user.groups.filter(name=self.group_name).exists()
        self.assertTrue(user_added_to_group, 'User should be added to group.')

    def test_join_nonexistent_user(self):
        try:
            XUser.join(self.http_req, 'nonexistent user', 'whatever group name')
        except Fault as e:
            self.assertEqual(e.faultCode, 404)

    def test_join_nonexistent_group(self):
        try:
            XUser.join(self.http_req, self.username, 'nonexistent group name')
        except Fault as e:
            self.assertEqual(e.faultCode, 404)


class TestUserUpdate(TestCase):
    '''Test User.update'''

    @classmethod
    def setUpClass(cls):
        cls.user = UserFactory(username='bob', email='bob@example.com')
        cls.user.set_password(cls.user.username)
        cls.user.save()

        cls.http_req = make_http_request(user=cls.user)
        cls.user_new_attrs = {
            'first_name': 'new first name',
            'last_name': 'new last name',
            'email': 'new email',
        }

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()

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
        try:
            XUser.update(self.http_req, new_values, self.user.pk)
        except Fault as e:
            self.assertEqual(e.faultCode, 403)

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

        try:
            XUser.update(self.http_req, user_new_attrs, test_user.pk)
        except Fault as e:
            self.assertEqual(e.faultCode, 403,
                             'Old password was not provided, ' +
                             'PermissionDenied should be catched.')

        user_new_attrs['old_password'] = 'invalid old password'
        try:
            XUser.update(self.http_req, user_new_attrs, test_user.pk)
        except Fault as e:
            self.assertEqual(e.faultCode, 403,
                             'Invalid old password was provided. ' +
                             'PermissionDenied should be catched.')

        user_new_attrs['old_password'] = test_user.username
        data = XUser.update(self.http_req, user_new_attrs, test_user.pk)
        self.assert_('password' not in data)
        self.assertEqual(data['first_name'], user_new_attrs['first_name'])
        self.assertEqual(data['last_name'], user_new_attrs['last_name'])
        self.assertEqual(data['email'], user_new_attrs['email'])

        user = User.objects.get(pk=test_user.pk)
        self.assert_(user.check_password(new_password))
