# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

import json
from http import HTTPStatus

from django.test import TestCase
from django.conf import settings
from django.test.client import Client
from django.urls import reverse

from tcms.management.models import EnvGroup
from tcms.management.models import EnvGroupPropertyMap
from tcms.management.models import EnvProperty
from tcms.management.models import Product, Version
from tcms.testplans.models import TestPlan
from tcms.tests import LoggedInTestCase
from tcms.tests import remove_perm_from_user
from tcms.tests import user_should_have_perm
from tcms.tests.factories import EnvGroupFactory
from tcms.tests.factories import EnvGroupPropertyMapFactory
from tcms.tests.factories import EnvPropertyFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import PlanTypeFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory


class TestVisitAndSearchGroupPage(LoggedInTestCase):
    """Test case for opening group page"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.group_url = reverse('mgmt-environment_groups')

        cls.group_1 = EnvGroupFactory(name='rhel-7')
        cls.group_2 = EnvGroupFactory(name='fedora')

        cls.property_1 = EnvPropertyFactory()
        cls.property_2 = EnvPropertyFactory()
        cls.property_3 = EnvPropertyFactory()

        EnvGroupPropertyMapFactory(group=cls.group_1, property=cls.property_1)
        EnvGroupPropertyMapFactory(group=cls.group_1, property=cls.property_2)
        EnvGroupPropertyMapFactory(group=cls.group_1, property=cls.property_3)

        EnvGroupPropertyMapFactory(group=cls.group_2, property=cls.property_1)
        EnvGroupPropertyMapFactory(group=cls.group_2, property=cls.property_3)

    def tearDown(self):
        remove_perm_from_user(self.tester, 'management.change_envgroup')

    def test_visit_group_page(self):
        response = self.client.get(self.group_url)

        for group in (self.group_1, self.group_2):
            self.assertContains(
                response,
                '<label class=" ">{}</label>'.format(group.name),
                html=True)

    def test_visit_group_page_with_permission(self):
        user_should_have_perm(self.tester, 'management.change_envgroup')
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

        self.assertContains(response,
                            '<label class=" ">{}</label>'.format(self.group_1.name),
                            html=True)
        self.assertNotContains(response,
                               '<label class=" ">{}</label>'.format(self.group_2.name),
                               html=True)

    def test_search_groups_no_name(self):
        response = self.client.get(self.group_url, {'action': 'search'})

        for group in [self.group_1, self.group_2]:
            self.assertContains(response,
                                '<label class=" ">{}</label>'.format(group.name),
                                html=True)


class TestAddGroup(LoggedInTestCase):
    """Test case for adding a group"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.group_add_url = reverse('mgmt-environment_groups')

        cls.new_group_name = 'nitrate-dev'

        cls.permission = 'management.add_envgroup'
        user_should_have_perm(cls.tester, cls.permission)

    def test_missing_permission(self):
        remove_perm_from_user(self.tester, self.permission)

        response = self.client.get(self.group_add_url,
                                   {'action': 'add', 'name': self.new_group_name})
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'Permission denied.'})

    def test_missing_group_name(self):
        response = self.client.get(self.group_add_url, {'action': 'add'})
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'Environment group name is required.'})

        response = self.client.get(self.group_add_url, {'action': 'add', 'name': ''})
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'Environment group name is required.'})

    def test_add_a_new_group(self):
        response = self.client.get(self.group_add_url,
                                   {'action': 'add', 'name': self.new_group_name})

        groups = EnvGroup.objects.filter(name=self.new_group_name)
        self.assertEqual(1, groups.count())

        new_group = groups[0]

        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 0, 'response': 'ok', 'id': new_group.pk})

    def test_add_existing_group(self):
        self.client.get(self.group_add_url,
                        {'action': 'add', 'name': self.new_group_name})

        response = self.client.get(self.group_add_url,
                                   {'action': 'add', 'name': self.new_group_name})
        response_data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertIn(
            "Environment group name '{}' already".format(self.new_group_name),
            response_data['response']
        )


class TestDeleteGroup(LoggedInTestCase):
    """Test case for deleting a group"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.group_delete_url = reverse('mgmt-environment_groups')
        cls.permission = 'management.delete_envgroup'
        user_should_have_perm(cls.tester, cls.permission)

        cls.group_nitrate = EnvGroupFactory(name='nitrate')
        cls.group_fedora = EnvGroupFactory(name='fedora')

    def tearDown(self):
        remove_perm_from_user(self.tester, self.permission)

    def test_able_to_delete_when_logged_in(self):
        response = self.client.get(self.group_delete_url,
                                   {'action': 'del', 'id': self.group_nitrate.pk})

        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 0, 'response': 'ok'})

        self.assertFalse(
            EnvGroup.objects.filter(pk=self.group_nitrate.pk).exists())

    def test_missing_permission_when_deleting_and_no_permission(self):
        remove_perm_from_user(self.tester, self.permission)
        response = self.client.get(self.group_delete_url,
                                   {'action': 'del', 'id': self.group_nitrate.pk})
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'Permission denied.'})

    def test_return_404_if_delete_a_nonexisting_group(self):
        response = self.client.get(self.group_delete_url,
                                   {'action': 'del', 'id': 9999999999})
        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)

    def test_return_404_if_no_id(self):
        response = self.client.get(self.group_delete_url,
                                   {'action': 'del'})
        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)

    def test_response_when_id_not_an_int(self):
        response = self.client.get(self.group_delete_url,
                                   {'action': 'del', 'id': 'NOT_AN_INT'})

        result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(result['rc'], 1)
        self.assertEqual(result['response'], 'id must be an integer.')


class TestModifyGroup(LoggedInTestCase):
    """Test case for modifying a group"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.group_nitrate = EnvGroupFactory(name='nitrate')

        cls.permission = 'management.change_envgroup'
        cls.group_modify_url = reverse('mgmt-environment_groups')

    def tearDown(self):
        remove_perm_from_user(self.tester, self.permission)

    def test_refuse_when_missing_permission(self):
        response = self.client.get(self.group_modify_url,
                                   {'action': 'modify',
                                    'id': self.group_nitrate.pk,
                                    'status': 0})
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'Permission denied.'})

    def test_refuse_invalid_status_value(self):
        user_should_have_perm(self.tester, self.permission)

        # Status value is not valid as long as it's not 0 or 1.
        for invalid_status in ('true', 'false', 'yes', 'no', '2'):
            response = self.client.get(self.group_modify_url,
                                       {'action': 'modify',
                                        'id': self.group_nitrate.pk,
                                        'status': invalid_status})
            self.assertJSONEqual(
                str(response.content, encoding=settings.DEFAULT_CHARSET),
                {'rc': 1, 'response': 'Argument illegal.'})

    def test_404_if_group_pk_not_exist(self):
        user_should_have_perm(self.tester, self.permission)
        response = self.client.get(self.group_modify_url,
                                   {'action': 'modify',
                                    'id': 999999999,
                                    'status': 1})
        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)

    def test_disable_a_group(self):
        user_should_have_perm(self.tester, self.permission)
        self.client.get(self.group_modify_url,
                        {'action': 'modify',
                         'id': self.group_nitrate.pk,
                         'status': 0})

        group = EnvGroup.objects.get(pk=self.group_nitrate.pk)
        self.assertFalse(group.is_active)


class TestVisitEnvironmentGroupPage(LoggedInTestCase):
    """Test case for visiting environment group page"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        user_should_have_perm(cls.tester, 'management.change_envgroup')

        cls.group_edit_url = reverse('mgmt-environment_group_edit')
        cls.group_nitrate = EnvGroupFactory(name='nitrate')
        cls.disabled_group = EnvGroupFactory(name='disabled-group',
                                             is_active=False)

    def test_404_when_missing_group_id(self):
        response = self.client.get(self.group_edit_url)
        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)

    def test_404_if_group_id_not_exist(self):
        response = self.client.get(self.group_edit_url, {'id': 9999999})
        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)

    def test_visit_a_group(self):
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
        response = self.client.get(self.group_edit_url, {'id': self.disabled_group.pk})

        self.assertContains(
            response,
            '<input name="name" value="{}" type="text">'.format(self.disabled_group.name),
            html=True)

        self.assertContains(
            response,
            '<input name="enabled" type="checkbox">',
            html=True)


class TestEditEnvironmentGroup(LoggedInTestCase):
    """Test case for editing environment group"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        user_should_have_perm(cls.tester, 'management.change_envgroup')

        cls.group_nitrate = EnvGroupFactory(name='nitrate')
        cls.duplicate_group = EnvGroupFactory(name='fedora')

        cls.property_1 = EnvPropertyFactory()
        cls.property_2 = EnvPropertyFactory()
        cls.property_3 = EnvPropertyFactory()

        cls.group_edit_url = reverse('mgmt-environment_group_edit')

    def test_refuse_if_there_is_duplicate_group_name(self):
        response = self.client.get(self.group_edit_url, {
            'action': 'modify',
            'id': self.group_nitrate.pk,
            'name': self.duplicate_group.name,
            'enabled': 'on'
        }, follow=True)

        self.assertContains(response, 'Environment group with the same name already exists')

    def test_edit_group(self):
        new_group_name = 'nitrate-dev'
        self.client.get(self.group_edit_url, {
            'action': 'modify',
            'id': self.group_nitrate.pk,
            'name': new_group_name,
            'enabled': True,
            'selected_property_ids': [self.property_1.pk, self.property_2.pk]
        })

        group = EnvGroup.objects.get(pk=self.group_nitrate.pk)
        self.assertEqual(new_group_name, group.name)
        self.assertTrue(group.is_active)
        self.assertTrue(EnvGroupPropertyMap.objects.filter(
            group_id=self.group_nitrate.pk, property_id=self.property_1.pk).exists())
        self.assertTrue(EnvGroupPropertyMap.objects.filter(
            group_id=self.group_nitrate.pk, property_id=self.property_2.pk).exists())


class TestAddProperty(LoggedInTestCase):
    """Test case for adding properties to a group"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.permission = 'management.add_envproperty'
        cls.group_properties_url = reverse('mgmt-environment_properties')

        cls.group_nitrate = EnvGroupFactory(name='nitrate')
        cls.duplicate_property = EnvPropertyFactory(name='f26')

    def setUp(self):
        super().setUp()
        user_should_have_perm(self.tester, self.permission)

    def test_refuse_if_missing_permission(self):
        remove_perm_from_user(self.tester, self.permission)
        response = self.client.get(self.group_properties_url, {'action': 'add'})

        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'Permission denied'})

    def test_refuse_if_missing_property_name(self):
        response = self.client.get(self.group_properties_url, {'action': 'add'})
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'Property name is required'})

        response = self.client.get(self.group_properties_url,
                                   {'action': 'add', 'name': ''})
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'Property name is required'})

    def test_refuse_to_create_duplicate_property(self):
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
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            expected_result)

    def test_add_new_property(self):
        new_property_name = 'f24'
        request_data = {
            'action': 'add',
            'name': new_property_name,
        }
        response = self.client.get(self.group_properties_url, request_data)

        self.assertTrue(EnvProperty.objects.filter(name=new_property_name).exists())

        new_property = EnvProperty.objects.get(name=new_property_name)
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 0, 'response': 'ok', 'name': new_property_name, 'id': new_property.pk})


class TestEditProperty(LoggedInTestCase):
    """Test case for editing a property"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.permission = 'management.change_envproperty'
        cls.group_properties_url = reverse('mgmt-environment_properties')
        cls.property = EnvPropertyFactory(name='f26')

    def setUp(self):
        super().setUp()
        user_should_have_perm(self.tester, self.permission)

    def test_refuse_if_missing_permission(self):
        remove_perm_from_user(self.tester, self.permission)
        response = self.client.get(self.group_properties_url,
                                   {'action': 'edit', 'id': self.property.pk})
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'Permission denied'})

    def test_refuse_if_missing_property_id(self):
        response = self.client.get(self.group_properties_url, {'action': 'edit'})

        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'ID is required'})

    def test_refuse_if_property_id_not_exist(self):
        response = self.client.get(self.group_properties_url,
                                   {'action': 'edit', 'id': 999999999})

        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'ID does not exist.'})

    def test_edit_a_property(self):
        new_property_name = 'fedora-24'
        response = self.client.get(self.group_properties_url,
                                   {'action': 'edit',
                                    'id': self.property.pk,
                                    'name': new_property_name})

        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 0, 'response': 'ok'})

        property = EnvProperty.objects.get(pk=self.property.pk)
        self.assertEqual(new_property_name, property.name)


class TestEnableDisableProperty(LoggedInTestCase):
    """Test case for modifying a property"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.permission = 'management.change_envproperty'
        cls.group_properties_url = reverse('mgmt-environment_properties')

        cls.group_nitrate = EnvGroupFactory(name='nitrate')

        cls.property_os = EnvPropertyFactory(name='OS')
        cls.property_lang = EnvPropertyFactory(name='lang')
        cls.disabled_property_1 = EnvPropertyFactory(name='disabled-property-1',
                                                     is_active=False)
        cls.disabled_property_2 = EnvPropertyFactory(name='disabled-property-2',
                                                     is_active=False)

        EnvGroupPropertyMapFactory(group=cls.group_nitrate,
                                   property=cls.property_os)
        EnvGroupPropertyMapFactory(group=cls.group_nitrate,
                                   property=cls.property_lang)
        EnvGroupPropertyMapFactory(group=cls.group_nitrate,
                                   property=cls.disabled_property_1)
        EnvGroupPropertyMapFactory(group=cls.group_nitrate,
                                   property=cls.disabled_property_2)

    def setUp(self):
        super().setUp()
        user_should_have_perm(self.tester, self.permission)

    def test_refuse_if_missing_permission(self):
        remove_perm_from_user(self.tester, self.permission)
        response = self.client.get(self.group_properties_url,
                                   {'action': 'modify', 'id': self.property_os.pk})

        self.assertContains(response, 'Permission denied')

    def test_refuse_if_status_is_illegal(self):
        for illegal_status in ('yes', 'no', '2', '-1'):
            response = self.client.get(self.group_properties_url,
                                       {'action': 'modify',
                                        'id': [self.property_os.pk,
                                               self.property_lang.pk],
                                        'status': illegal_status})

            self.assertContains(response, 'Argument illegal')

            self.assertTrue(
                EnvGroupPropertyMap.objects.filter(
                    group=self.group_nitrate,
                    property=self.property_os).exists())

            self.assertTrue(
                EnvGroupPropertyMap.objects.filter(
                    group=self.group_nitrate,
                    property=self.property_lang).exists())

    def test_enable_a_property(self):
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
            EnvProperty.objects.get(pk=self.disabled_property_1.pk).is_active)
        self.assertTrue(
            EnvProperty.objects.get(pk=self.disabled_property_2.pk).is_active)

    def test_disable_a_property(self):
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
            EnvProperty.objects.get(pk=self.property_os.pk).is_active)
        self.assertFalse(
            EnvProperty.objects.get(pk=self.property_lang.pk).is_active)

        self.assertFalse(
            EnvGroupPropertyMap.objects.filter(
                group=self.group_nitrate, property=self.property_os).exists())
        self.assertFalse(
            EnvGroupPropertyMap.objects.filter(
                group=self.group_nitrate, property=self.property_lang).exists())


class ProductTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(username='admin', email='admin@example.com')
        cls.user.set_password('admin')  # nosec:B106:hardcoded_password_funcarg
        cls.user.is_superuser = True
        cls.user.is_staff = True  # enables access to admin panel
        cls.user.save()

        cls.c = Client()
        cls.c.login(username='admin', password='admin')  # nosec:B106:hardcoded_password_funcarg

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
        """
        # setup
        product = ProductFactory(name='Something to delete')
        product_version = VersionFactory(value='0.1', product=product)
        plan_type = PlanTypeFactory()

        # create Test Plan via the UI by sending a POST request to the view
        previous_plans_count = TestPlan.objects.count()
        test_plan_name = 'Test plan for the new product'
        response = self.c.post(reverse('plans-new'), {
            'name': test_plan_name,
            'product': product.pk,
            'product_version': product_version.pk,
            'type': plan_type.pk,
        }, follow=True)
        self.assertEqual(HTTPStatus.OK, response.status_code)
        # verify test plan was created
        self.assertTrue(test_plan_name in str(response.content,
                                              encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(previous_plans_count + 1, TestPlan.objects.count())

        # now delete the product
        admin_delete_url = "admin:%s_%s_delete" % (product._meta.app_label,
                                                   product._meta.model_name)
        location = reverse(admin_delete_url, args=[product.pk])
        response = self.c.get(location)
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertTrue('Are you sure you want to delete the product "%s"' % product.name
                        in str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertTrue("Yes, I'm sure" in str(response.content,
                                               encoding=settings.DEFAULT_CHARSET))

        # confirm that we're sure we want to delete it
        response = self.c.post(location, {'post': 'yes'})
        self.assertEqual(302, response.status_code)
        self.assertTrue('/admin/%s/%s/' % (product._meta.app_label, product._meta.model_name)
                        in response['Location'])

        # verify everything has been deleted
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())
        self.assertFalse(Version.objects.filter(pk=product_version.pk).exists())
        self.assertEqual(previous_plans_count, TestPlan.objects.count())
