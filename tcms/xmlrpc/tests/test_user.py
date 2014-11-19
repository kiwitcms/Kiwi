# -*- coding: utf-8 -*-

from xmlrpclib import Fault

from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.test import TestCase

import tcms.xmlrpc.api.user as XUser

from tcms.xmlrpc.tests.utils import make_http_request
from tcms.xmlrpc.tests.utils import user_should_have_perm


class TestUserSerializer(TestCase):
    '''Test User.get_user_dict'''

    def setUp(self):
        self.http_req = make_http_request()

    def test_ensure_password_not_returned(self):
        test_user = self.http_req.user
        data = XUser.get_user_dict(test_user)
        self.assertEqual(data['username'], test_user.username)
        self.assertEqual(data['email'], test_user.email)
        self.assert_('password' not in data)


class TestUserFilter(TestCase):
    '''Test User.filter'''

    def setUp(self):
        self.user1 = User.objects.create(username='user 1',
                                         email='user1@exmaple.com',
                                         is_active=True)
        self.user2 = User.objects.create(username='user 2',
                                         email='user2@example.com',
                                         is_active=False)
        self.user3 = User.objects.create(username='user 3',
                                         email='user3@example.com',
                                         is_active=True)

        self.group_tester = Group.objects.create(name='Tester')
        self.group_reviewer = Group.objects.create(name='Reviewer')

        self.user1.groups.add(self.group_tester)
        self.user2.groups.add(self.group_reviewer)
        self.user3.groups.add(self.group_reviewer)

        self.http_req = make_http_request()

    def tearDown(self):
        self.user1.groups.clear()
        self.user2.groups.clear()
        self.user3.groups.clear()
        self.group_tester.delete()
        self.group_reviewer.delete()
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()

    def test_normal_search(self):
        users = XUser.filter(self.http_req, {'email': 'user2@example.com'})
        self.assertEqual(len(users), 1)
        for user in users:
            self.assertEqual(user['id'], self.user2.pk)
            self.assertEqual(user['username'], self.user2.username)

        users = XUser.filter(self.http_req, {
            'username__startswith': 'user ',
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

    def setUp(self):
        self.http_req = make_http_request(user_perm='auth.change_user')
        self.username = 'test_username'
        self.user = User.objects.create(username=self.username,
                                        email='username@example.com')
        self.group_name = 'test_group'
        self.group = Group.objects.create(name=self.group_name)

    def tearDown(self):
        self.user.groups.clear()
        self.group.delete()
        self.user.delete()

    def test_join_normally(self):
        XUser.join(self.http_req, self.username, self.group_name)

        user = User.objects.get(username=self.username)
        user_added_to_group = user.groups.filter(name=self.group_name).exists()
        self.assert_(user_added_to_group, 'User should be added to group.')

    def test_join_nonexistent_user(self):
        try:
            XUser.join(self.http_req,
                       'nonexistent user', 'whatever group name')
        except Fault as e:
            self.assertEqual(e.faultCode, 404)

    def test_join_nonexistent_group(self):
        try:
            XUser.join(self.http_req, self.username, 'nonexistent group name')
        except Fault as e:
            self.assertEqual(e.faultCode, 404)


class TestUserUpdate(TestCase):
    '''Test User.update'''

    def setUp(self):
        self.user = User.objects.create(username='bob',
                                        email='bob@example.com')
        self.user.set_password(self.user.username)
        self.user.save()

        self.http_req = make_http_request()
        self.user_new_attrs = {
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
