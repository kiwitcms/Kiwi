# -*- coding: utf-8 -*-

import json
import httplib
from six.moves import http_client

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from tcms.core.logs.models import TCMSLogModel
from tcms.management.models import TCMSEnvGroup
from tcms.management.models import TCMSEnvGroupPropertyMap
from tcms.management.models import TCMSEnvProperty
from tcms.management.models import Product, Version
from tcms.testplans.models import TestPlan, _listen, _disconnect_signals
from tcms.tests import remove_perm_from_user
from tcms.tests import user_should_have_perm
from tcms.tests.factories import TCMSEnvGroupFactory
from tcms.tests.factories import TCMSEnvGroupPropertyMapFactory
from tcms.tests.factories import TCMSEnvPropertyFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestPlanTypeFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory


class TestVisitAndSearchGroupPage(TestCase):
    """Test case for opening group page"""

    @classmethod
    def setUpTestData(cls):
        super(TestVisitAndSearchGroupPage, cls).setUpTestData()

        cls.group_url = reverse('mgmt-environment_groups')

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
        group_edit_url = reverse('mgmt-environment_group_edit')

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

        cls.group_add_url = reverse('mgmt-environment_groups')

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

        cls.group_delete_url = reverse('mgmt-environment_groups')
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
        cls.group_modify_url = reverse('mgmt-environment_groups')

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

        self.client.get(self.group_modify_url,
                        {'action': 'modify',
                         'id': self.group_nitrate.pk,
                         'status': 0})

        group = TCMSEnvGroup.objects.get(pk=self.group_nitrate.pk)
        self.assertFalse(group.is_active)


class TestVisitEnvironmentGroupPage(TestCase):
    """Test case for visiting environment group page"""

    @classmethod
    def setUpTestData(cls):
        super(TestVisitEnvironmentGroupPage, cls).setUpTestData()

        cls.tester = User.objects.create_user(username='tester',
                                              email='tester@example.com',
                                              password='password')
        user_should_have_perm(cls.tester, 'management.change_tcmsenvgroup')

        cls.group_edit_url = reverse('mgmt-environment_group_edit')
        cls.group_nitrate = TCMSEnvGroupFactory(name='nitrate', manager=cls.tester)
        cls.disabled_group = TCMSEnvGroupFactory(name='disabled-group',
                                                 is_active=False,
                                                 manager=cls.tester)

    def test_404_when_missing_group_id(self):
        self.client.login(username=self.tester.username, password='password')
        response = self.client.get(self.group_edit_url)
        self.assertEqual(http_client.NOT_FOUND, response.status_code)

    def test_404_if_group_id_not_exist(self):
        self.client.login(username=self.tester.username, password='password')
        response = self.client.get(self.group_edit_url, {'id': 9999999})
        self.assertEqual(http_client.NOT_FOUND, response.status_code)

    def test_visit_a_group(self):
        self.client.login(username=self.tester.username, password='password')

        response = self.client.get(self.group_edit_url, {'id': self.group_nitrate.pk})

        self.assertContains(
            response,
            '<input name="name" value="{}" type="text">'.format(self.group_nitrate.name),
            html=True)

        self.assertContains(
            response,
            '<input name="enabled" type="checkbox" checked>',
            html=True)

    def test_visit_disabled_group(self):
        self.client.login(username=self.tester.username, password='password')

        response = self.client.get(self.group_edit_url, {'id': self.disabled_group.pk})

        self.assertContains(
            response,
            '<input name="name" value="{}" type="text">'.format(self.disabled_group.name),
            html=True)

        self.assertContains(
            response,
            '<input name="enabled" type="checkbox">',
            html=True)


class TestEditEnvironmentGroup(TestCase):
    """Test case for editing environment group"""

    @classmethod
    def setUpTestData(cls):
        super(TestEditEnvironmentGroup, cls).setUpTestData()

        cls.tester = User.objects.create_user(username='tester',
                                              email='tester@example.com',
                                              password='password')
        user_should_have_perm(cls.tester, 'management.change_tcmsenvgroup')

        cls.group_nitrate = TCMSEnvGroupFactory(name='nitrate', manager=cls.tester)
        cls.duplicate_group = TCMSEnvGroupFactory(name='fedora', manager=cls.tester)

        cls.property_1 = TCMSEnvPropertyFactory()
        cls.property_2 = TCMSEnvPropertyFactory()
        cls.property_3 = TCMSEnvPropertyFactory()

        cls.group_edit_url = reverse('mgmt-environment_group_edit')

    def test_refuse_if_there_is_duplicate_group_name(self):
        self.client.login(username=self.tester.username, password='password')

        response = self.client.get(self.group_edit_url, {
            'action': 'modify',
            'id': self.group_nitrate.pk,
            'name': self.duplicate_group.name,
            'enabled': 'on'
        })

        self.assertContains(response, 'Duplicated name already exists')

    def test_edit_group(self):
        self.client.login(username=self.tester.username, password='password')

        new_group_name = 'nitrate-dev'
        self.client.get(self.group_edit_url, {
            'action': 'modify',
            'id': self.group_nitrate.pk,
            'name': new_group_name,
            'enabled': 'on',
            'selected_property_ids': [self.property_1.pk, self.property_2.pk]
        })

        group = TCMSEnvGroup.objects.get(pk=self.group_nitrate.pk)
        self.assertEqual(new_group_name, group.name)
        self.assertTrue(group.is_active)
        self.assertTrue(TCMSEnvGroupPropertyMap.objects.filter(
            group_id=self.group_nitrate.pk, property_id=self.property_1.pk).exists())
        self.assertTrue(TCMSEnvGroupPropertyMap.objects.filter(
            group_id=self.group_nitrate.pk, property_id=self.property_2.pk).exists())


class TestAddProperty(TestCase):
    """Test case for adding properties to a group"""

    @classmethod
    def setUpTestData(cls):
        super(TestAddProperty, cls).setUpTestData()

        cls.permission = 'management.add_tcmsenvproperty'
        cls.group_properties_url = reverse('mgmt-environment_properties')

        cls.tester = User.objects.create_user(username='tester',
                                              email='tester@example.com',
                                              password='password')

        cls.group_nitrate = TCMSEnvGroupFactory(name='nitrate', manager=cls.tester)
        cls.duplicate_property = TCMSEnvPropertyFactory(name='f26')

    def setUp(self):
        user_should_have_perm(self.tester, self.permission)

    def test_refuse_if_missing_permission(self):
        remove_perm_from_user(self.tester, self.permission)
        self.client.login(username=self.tester.username, password='password')

        response = self.client.get(self.group_properties_url, {'action': 'add'})

        self.assertEqual({'rc': 1, 'response': 'Permission denied'},
                         json.loads(response.content))

    def test_refuse_if_missing_property_name(self):
        self.client.login(username=self.tester.username, password='password')

        response = self.client.get(self.group_properties_url, {'action': 'add'})
        self.assertEqual({'rc': 1, 'response': 'Property name is required'},
                         json.loads(response.content))

        response = self.client.get(self.group_properties_url,
                                   {'action': 'add', 'name': ''})
        self.assertEqual({'rc': 1, 'response': 'Property name is required'},
                         json.loads(response.content))

    def test_refuse_to_create_duplicate_property(self):
        self.client.login(username=self.tester.username, password='password')

        request_data = {
            'action': 'add',
            'name': self.duplicate_property.name,
        }
        response = self.client.get(self.group_properties_url, request_data)

        expected_result = {
            'rc': 1,
            'response': "Environment property named '{}' already exists, "
                        "please select another name.".format(self.duplicate_property.name)
        }
        self.assertEqual(expected_result, json.loads(response.content))

    def test_add_new_property(self):
        self.client.login(username=self.tester.username, password='password')

        new_property_name = 'f24'
        request_data = {
            'action': 'add',
            'name': new_property_name,
        }
        response = self.client.get(self.group_properties_url, request_data)

        self.assertTrue(TCMSEnvProperty.objects.filter(name=new_property_name).exists())

        new_property = TCMSEnvProperty.objects.get(name=new_property_name)
        self.assertEqual({'rc': 0, 'response': 'ok',
                          'name': new_property_name, 'id': new_property.pk},
                         json.loads(response.content))


class TestEditProperty(TestCase):
    """Test case for editing a property"""

    @classmethod
    def setUpTestData(cls):
        super(TestEditProperty, cls).setUpTestData()

        cls.permission = 'management.change_tcmsenvproperty'
        cls.group_properties_url = reverse('mgmt-environment_properties')

        cls.tester = User.objects.create_user(username='tester',
                                              email='tester@example.com',
                                              password='password')

        cls.property = TCMSEnvPropertyFactory(name='f26')

    def setUp(self):
        user_should_have_perm(self.tester, self.permission)

    def test_refuse_if_missing_permission(self):
        remove_perm_from_user(self.tester, self.permission)
        self.client.login(username=self.tester.username, password='password')

        response = self.client.get(self.group_properties_url,
                                   {'action': 'edit', 'id': self.property.pk})
        self.assertEqual({'rc': 1, 'response': 'Permission denied'},
                         json.loads(response.content))

    def test_refuse_if_missing_property_id(self):
        self.client.login(username=self.tester.username, password='password')

        response = self.client.get(self.group_properties_url, {'action': 'edit'})

        self.assertEqual({'rc': 1, 'response': 'ID is required'},
                         json.loads(response.content))

    def test_refuse_if_property_id_not_exist(self):
        self.client.login(username=self.tester.username, password='password')

        response = self.client.get(self.group_properties_url,
                                   {'action': 'edit', 'id': 999999999})

        self.assertEqual({'rc': 1, 'response': 'ID does not exist.'},
                         json.loads(response.content))

    def test_edit_a_property(self):
        self.client.login(username=self.tester.username, password='password')

        new_property_name = 'fedora-24'
        response = self.client.get(self.group_properties_url,
                                   {'action': 'edit',
                                    'id': self.property.pk,
                                    'name': new_property_name})

        self.assertEqual({'rc': 0, 'response': 'ok'}, json.loads(response.content))

        property = TCMSEnvProperty.objects.get(pk=self.property.pk)
        self.assertEqual(new_property_name, property.name)


class TestEnableDisableProperty(TestCase):
    """Test case for modifying a property"""

    @classmethod
    def setUpTestData(cls):
        super(TestEnableDisableProperty, cls).setUpTestData()

        cls.permission = 'management.change_tcmsenvproperty'
        cls.group_properties_url = reverse('mgmt-environment_properties')

        cls.tester = User.objects.create_user(username='tester',
                                              email='tester@example.com',
                                              password='password')

        cls.group_nitrate = TCMSEnvGroupFactory(name='nitrate')

        cls.property_os = TCMSEnvPropertyFactory(name='OS')
        cls.property_lang = TCMSEnvPropertyFactory(name='lang')
        cls.disabled_property_1 = TCMSEnvPropertyFactory(name='disabled-property-1',
                                                         is_active=False)
        cls.disabled_property_2 = TCMSEnvPropertyFactory(name='disabled-property-2',
                                                         is_active=False)

        TCMSEnvGroupPropertyMapFactory(group=cls.group_nitrate,
                                       property=cls.property_os)
        TCMSEnvGroupPropertyMapFactory(group=cls.group_nitrate,
                                       property=cls.property_lang)
        TCMSEnvGroupPropertyMapFactory(group=cls.group_nitrate,
                                       property=cls.disabled_property_1)
        TCMSEnvGroupPropertyMapFactory(group=cls.group_nitrate,
                                       property=cls.disabled_property_2)

    def setUp(self):
        user_should_have_perm(self.tester, self.permission)

    def test_refuse_if_missing_permission(self):
        remove_perm_from_user(self.tester, self.permission)
        self.client.login(username=self.tester.username, password='password')

        response = self.client.get(self.group_properties_url,
                                   {'action': 'modify', 'id': self.property_os.pk})

        self.assertContains(response, 'Permission denied')

    def test_refuse_if_status_is_illegal(self):
        self.client.login(username=self.tester.username, password='password')

        for illegal_status in ('yes', 'no', '2', '-1'):
            response = self.client.get(self.group_properties_url,
                                       {'action': 'modify',
                                        'id': [self.property_os.pk,
                                               self.property_lang.pk],
                                        'status': illegal_status})

            self.assertContains(response, 'Argument illegal')

            self.assertTrue(
                TCMSEnvGroupPropertyMap.objects.filter(
                    group=self.group_nitrate,
                    property=self.property_os).exists())

            self.assertTrue(
                TCMSEnvGroupPropertyMap.objects.filter(
                    group=self.group_nitrate,
                    property=self.property_lang).exists())

    def test_enable_a_property(self):
        self.client.login(username=self.tester.username, password='password')

        response = self.client.get(self.group_properties_url,
                                   {'action': 'modify',
                                    'id': [self.disabled_property_1.pk,
                                           self.disabled_property_2.pk],
                                    'status': 1})

        self.assertContains(
            response,
            "Modify test properties status &#39;{}&#39; successfully.".format(
                "&#39;, &#39;".join([self.disabled_property_1.name,
                                     self.disabled_property_2.name])))

        self.assertTrue(
            TCMSEnvProperty.objects.get(pk=self.disabled_property_1.pk).is_active)
        self.assertTrue(
            TCMSEnvProperty.objects.get(pk=self.disabled_property_2.pk).is_active)

    def test_disable_a_property(self):
        self.client.login(username=self.tester.username, password='password')

        response = self.client.get(self.group_properties_url,
                                   {'action': 'modify',
                                    'id': [self.property_os.pk,
                                           self.property_lang.pk],
                                    'status': 0})

        self.assertContains(
            response,
            "Modify test properties status &#39;{}&#39; successfully.".format(
                "&#39;, &#39;".join([self.property_os.name,
                                     self.property_lang.name])))

        self.assertFalse(
            TCMSEnvProperty.objects.get(pk=self.property_os.pk).is_active)
        self.assertFalse(
            TCMSEnvProperty.objects.get(pk=self.property_lang.pk).is_active)

        self.assertFalse(
            TCMSEnvGroupPropertyMap.objects.filter(
                group=self.group_nitrate, property=self.property_os).exists())
        self.assertFalse(
            TCMSEnvGroupPropertyMap.objects.filter(
                group=self.group_nitrate, property=self.property_lang).exists())


class ProductTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(username='admin', email='admin@example.com')
        cls.user.set_password('admin')
        cls.user.is_superuser = True
        cls.user.is_staff = True  # enables access to admin panel
        cls.user.save()

        cls.c = Client()
        cls.c.login(username='admin', password='admin')

    def test_product_delete_with_test_plan_wo_email_settings(self):
        """
            A test to demonstrate Issue #181.

            Steps to reproduce:
            1) Create a new Product
            2) Create a new Test Plan for Product
            3) DON'T edit the Test Plan
            4) Delete the Product

            Expected results:
            0) No errors
            1) Product is deleted
            2) Test Plan is deleted

            NOTE: we manually connect signals handlers here
            b/c in est mode LISTENING_MODEL_SIGNAL = False
        """
        # connect signal handlers
        _listen()

        try:
            # setup
            product = ProductFactory(name='Something to delete')
            product_version = VersionFactory(value='0.1', product=product)
            plan_type = TestPlanTypeFactory()

            # create Test Plan via the UI by sending a POST request to the view
            previous_plans_count = TestPlan.objects.count()
            test_plan_name = 'Test plan for the new product'
            response = self.c.post(reverse('plans-new'), {
                'name': test_plan_name,
                'product': product.pk,
                'product_version': product_version.pk,
                'type': plan_type.pk,
            }, follow=True)
            self.assertEqual(httplib.OK, response.status_code)
            # verify test plan was created
            self.assertTrue(test_plan_name in response.content)
            self.assertEqual(previous_plans_count + 1, TestPlan.objects.count())

            # now delete the product
            admin_delete_url = "admin:%s_%s_delete" % (product._meta.app_label, product._meta.model_name)
            location = reverse(admin_delete_url, args=[product.pk])
            response = self.c.get(location)
            self.assertEqual(httplib.OK, response.status_code)
            self.assertTrue('Are you sure you want to delete the product "%s"' % product.name in response.content)
            self.assertTrue("Yes, I'm sure" in response.content)

            # confirm that we're sure we want to delete it
            response = self.c.post(location, {'post': 'yes'})
            self.assertEqual(302, response.status_code)
            self.assertTrue('/admin/%s/%s/' % (product._meta.app_label, product._meta.model_name) in response['Location'])

            # verify everything has been deleted
            self.assertFalse(Product.objects.filter(pk=product.pk).exists())
            self.assertFalse(Version.objects.filter(pk=product_version.pk).exists())
            self.assertEqual(previous_plans_count, TestPlan.objects.count())
        finally:
            # disconnect signals to avoid influencing other tests
            _disconnect_signals()
