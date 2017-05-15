# -*- coding: utf-8 -*-

import json

from six.moves import http_client

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from tcms.management.models import TCMSEnvGroup
from tcms.management.models import TCMSEnvGroupPropertyMap
from tcms.core.logs.models import TCMSLogModel
from tcms.tests import remove_perm_from_user
from tcms.tests import user_should_have_perm
from tcms.tests.factories import TCMSEnvGroupFactory
from tcms.tests.factories import TCMSEnvGroupPropertyMapFactory
from tcms.tests.factories import TCMSEnvPropertyFactory


class TestVisitAndSearchGroupPage(TestCase):
    """Test case for opening group page"""

    @classmethod
    def setUpTestData(cls):
        super(TestVisitAndSearchGroupPage, cls).setUpTestData()

        cls.group_url = reverse('tcms.management.views.environment_groups')

        cls.new_tester = User.objects.create_user(username='new-tester',
                                                  email='new-tester@example.com',
                                                  password='password')

        cls.group_1 = TCMSEnvGroupFactory(name='rhel-7',
                                          manager=cls.new_tester,
                                          modified_by=None)
        cls.group_2 = TCMSEnvGroupFactory(name='fedora',
                                          manager=cls.new_tester,
                                          modified_by=None)

        cls.group_1.log_action(who=cls.new_tester,
                               action='Add group {}'.format(cls.group_1.name))
        cls.group_1.log_action(who=cls.new_tester,
                               action='Edit group {}'.format(cls.group_1.name))
        cls.group_2.log_action(who=cls.new_tester,
                               action='Edit group {}'.format(cls.group_2.name))

        cls.property_1 = TCMSEnvPropertyFactory()
        cls.property_2 = TCMSEnvPropertyFactory()
        cls.property_3 = TCMSEnvPropertyFactory()

        TCMSEnvGroupPropertyMapFactory(group=cls.group_1, property=cls.property_1)
        TCMSEnvGroupPropertyMapFactory(group=cls.group_1, property=cls.property_2)
        TCMSEnvGroupPropertyMapFactory(group=cls.group_1, property=cls.property_3)

        TCMSEnvGroupPropertyMapFactory(group=cls.group_2, property=cls.property_1)
        TCMSEnvGroupPropertyMapFactory(group=cls.group_2, property=cls.property_3)

    def tearDown(self):
        remove_perm_from_user(self.new_tester, 'management.change_tcmsenvgroup')

    def assert_group_logs_are_displayed(self, response, group):
        env_group_ct = ContentType.objects.get_for_model(TCMSEnvGroup)
        logs = TCMSLogModel.objects.filter(content_type=env_group_ct,
                                           object_pk=group.pk)

        for log in logs:
            self.assertContains(
                response,
                '<div class="envlog_who">{}</div>'.format(log.who.username),
                html=True)
            self.assertContains(
                response,
                '<div class="envlog_content">{}</div>'.format(log.action),
                html=True)

    def test_visit_group_page(self):
        response = self.client.get(self.group_url)

        for group in (self.group_1, self.group_2):
            self.assertContains(
                response,
                '<label class=" ">{}</label>'.format(group.name),
                html=True)

            self.assert_group_logs_are_displayed(response, group)

    def test_visit_group_page_with_permission(self):
        self.client.login(username=self.new_tester.username, password='password')

        user_should_have_perm(self.new_tester, 'management.change_tcmsenvgroup')
        group_edit_url = reverse('tcms.management.views.environment_group_edit')

        response = self.client.get(self.group_url)

        for group in (self.group_1, self.group_2):
            self.assertContains(
                response,
                '<a href="{}?id={}">{}</a>'.format(group_edit_url,
                                                   group.pk,
                                                   group.name),
                html=True)

    def test_search_groups(self):
        response = self.client.get(self.group_url, {'action': 'search', 'name': 'el'})

        self.assertContains(
            response,
            '<label class=" ">{}</label>'.format(self.group_1.name),
            html=True)
        self.assertNotContains(
            response,
            '<label class=" ">{}</label>'.format(self.group_2.name),
            html=True)


class TestAddGroup(TestCase):
    """Test case for adding a group"""

    @classmethod
    def setUpTestData(cls):
        super(TestAddGroup, cls).setUpTestData()

        cls.group_add_url = reverse('tcms.management.views.environment_groups')

        cls.tester = User.objects.create_user(username='new-tester',
                                              email='new-tester@example.com',
                                              password='password')

        cls.new_group_name = 'nitrate-dev'

        cls.permission = 'management.add_tcmsenvgroup'
        user_should_have_perm(cls.tester, cls.permission)

    def test_missing_permission(self):
        remove_perm_from_user(self.tester, self.permission)

        response = self.client.get(self.group_add_url,
                                   {'action': 'add', 'name': self.new_group_name})
        self.assertEqual({'rc': 1, 'response': 'Permission denied.'},
                         json.loads(response.content))

    def test_missing_group_name(self):
        self.client.login(username=self.tester, password='password')

        response = self.client.get(self.group_add_url, {'action': 'add'})
        self.assertEqual({'rc': 1, 'response': 'Environment group name is required.'},
                         json.loads(response.content))

        response = self.client.get(self.group_add_url, {'action': 'add', 'name': ''})
        self.assertEqual({'rc': 1, 'response': 'Environment group name is required.'},
                         json.loads(response.content))

    def test_add_a_new_group(self):
        self.client.login(username=self.tester, password='password')
        response = self.client.get(self.group_add_url,
                                   {'action': 'add', 'name': self.new_group_name})
        response_data = json.loads(response.content)

        groups = TCMSEnvGroup.objects.filter(name=self.new_group_name)
        self.assertEqual(1, groups.count())

        new_group = groups[0]

        self.assertEqual(self.tester, new_group.manager)
        self.assertEqual({'rc': 0, 'response': 'ok', 'id': new_group.pk}, response_data)

        # Assert log is created for new group
        env_group_ct = ContentType.objects.get_for_model(TCMSEnvGroup)
        log = TCMSLogModel.objects.filter(content_type=env_group_ct,
                                          object_pk=new_group.pk)[0]
        self.assertEqual('Initial env group {}'.format(self.new_group_name),
                         log.action)

    def test_add_existing_group(self):
        self.client.login(username=self.tester, password='password')

        self.client.get(self.group_add_url,
                        {'action': 'add', 'name': self.new_group_name})

        response = self.client.get(self.group_add_url,
                                   {'action': 'add', 'name': self.new_group_name})
        response_data = json.loads(response.content)
        self.assertIn(
            "Environment group name '{}' already".format(self.new_group_name),
            response_data['response']
        )


class TestDeleteGroup(TestCase):
    """Test case for deleting a group"""

    @classmethod
    def setUpTestData(cls):
        super(TestDeleteGroup, cls).setUpTestData()

        cls.group_delete_url = reverse('tcms.management.views.environment_groups')
        cls.permission = 'management.delete_tcmsenvgroup'

        cls.tester = User.objects.create_user(username='tester',
                                              email='tester@exmaple.com',
                                              password='password')
        cls.group_manager = User.objects.create_user(username='group-manager',
                                                     email='manager@example.com',
                                                     password='password')

        cls.group_nitrate = TCMSEnvGroupFactory(name='nitrate',
                                                manager=cls.group_manager)
        cls.group_fedora = TCMSEnvGroupFactory(name='fedora',
                                               manager=cls.group_manager)

    def tearDown(self):
        remove_perm_from_user(self.tester, self.permission)

    def test_manager_is_able_to_delete_without_requiring_permission(self):
        self.client.login(username=self.group_manager.username,
                          password='password')

        response = self.client.get(self.group_delete_url,
                                   {'action': 'del', 'id': self.group_nitrate.pk})

        self.assertEqual({'rc': 0, 'response': 'ok'}, json.loads(response.content))

        self.assertFalse(
            TCMSEnvGroup.objects.filter(pk=self.group_nitrate.pk).exists())

    def test_missing_permission_when_delete_by_non_manager(self):
        self.client.login(username=self.tester.username, password='password')
        response = self.client.get(self.group_delete_url,
                                   {'action': 'del', 'id': self.group_nitrate.pk})
        self.assertEqual({'rc': 1, 'response': 'Permission denied.'},
                         json.loads(response.content))

    def test_delete_group_by_non_manager(self):
        user_should_have_perm(self.tester, self.permission)
        self.client.login(username=self.tester.username, password='password')

        response = self.client.get(self.group_delete_url,
                                   {'action': 'del', 'id': self.group_fedora.pk})

        self.assertEqual({'rc': 0, 'response': 'ok'}, json.loads(response.content))

        self.assertFalse(
            TCMSEnvGroup.objects.filter(pk=self.group_fedora.pk).exists())

    def test_return_404_if_delete_a_nonexisting_group(self):
        self.client.login(username=self.tester.username,
                          password='password')
        response = self.client.get(self.group_delete_url,
                                   {'action': 'del', 'id': 9999999999})
        self.assertEqual(http_client.NOT_FOUND, response.status_code)


class TestModifyGroup(TestCase):
    """Test case for modifying a group"""

    @classmethod
    def setUpTestData(cls):
        super(TestModifyGroup, cls).setUpTestData()

        cls.tester = User.objects.create_user(username='tester',
                                              email='tester@exmaple.com',
                                              password='password')

        cls.group_nitrate = TCMSEnvGroupFactory(name='nitrate', manager=cls.tester)

        cls.permission = 'management.change_tcmsenvgroup'
        cls.group_modify_url = reverse('tcms.management.views.environment_groups')

    def tearDown(self):
        remove_perm_from_user(self.tester, self.permission)

    def test_refuse_when_missing_permission(self):
        response = self.client.get(self.group_modify_url,
                                   {'action': 'modify',
                                    'id': self.group_nitrate.pk,
                                    'status': 0})
        self.assertEqual({'rc': 1, 'response': 'Permission denied.'},
                         json.loads(response.content))

    def test_refuse_invalid_status_value(self):
        user_should_have_perm(self.tester, self.permission)
        self.client.login(username=self.tester.username, password='password')

        # Status value is not valid as long as it's not 0 or 1.
        for invalid_status in ('true', 'false', 'yes', 'no', '2'):
            response = self.client.get(self.group_modify_url,
                                       {'action': 'modify',
                                        'id': self.group_nitrate.pk,
                                        'status': invalid_status})
            self.assertEqual({'rc': 1, 'response': 'Argument illegel.'},
                             json.loads(response.content))

    def test_404_if_group_pk_not_exist(self):
        user_should_have_perm(self.tester, self.permission)
        self.client.login(username=self.tester.username, password='password')

        response = self.client.get(self.group_modify_url,
                                   {'action': 'modify',
                                    'id': 999999999,
                                    'status': 1})
        self.assertEqual(http_client.NOT_FOUND, response.status_code)

    def test_disable_a_group(self):
        user_should_have_perm(self.tester, self.permission)
        self.client.login(username=self.tester.username, password='password')

        response = self.client.get(self.group_modify_url,
                                   {'action': 'modify',
                                    'id': self.group_nitrate.pk,
                                    'status': 0})

        group = TCMSEnvGroup.objects.get(pk=self.group_nitrate.pk)
        self.assertFalse(group.is_active)
