# -*- coding: utf-8 -*-

import unittest

from http.client import BAD_REQUEST
from http.client import NOT_FOUND
from http.client import FORBIDDEN
from http.client import NOT_IMPLEMENTED

from django.test import TestCase

from tcms.xmlrpc.api import product
from tcms.xmlrpc.tests.utils import make_http_request

from tcms.tests.factories import ComponentFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestBuildFactory
from tcms.tests.factories import TestCaseCategoryFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import TestTagFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestCheckCategory(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.product_nitrate = ProductFactory(name='nitrate')
        cls.product_xmlrpc = ProductFactory(name='xmlrpc')
        cls.case_categories = [
            TestCaseCategoryFactory(name='auto', product=cls.product_nitrate),
            TestCaseCategoryFactory(name='manual', product=cls.product_nitrate),
            TestCaseCategoryFactory(name='pending', product=cls.product_xmlrpc),
        ]

    def test_check_category(self):
        cat = product.check_category(None, 'manual', self.product_nitrate.pk)
        self.assertEqual(cat['name'], 'manual')

    def test_check_category_with_non_exist_category(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.check_category,
                                     None, "NonExist", self.product_nitrate.pk)
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.check_category, None, "--default--", 9999)

    def test_check_category_with_no_args(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.check_category, None, "--default--", None)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.check_category, None, "--default--", [])
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.check_category, None, "--default--", {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.check_category, None, "--default--", ())

    def test_no_category_queried_by_special_name(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.check_category,
                                     None, None, self.product_nitrate.name)
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.check_category,
                                     [], None, self.product_nitrate.name)
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.check_category,
                                     {}, None, self.product_nitrate.name)
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.check_category,
                                     (), None, self.product_nitrate.name)


class TestCheckComponent(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.product_nitrate = ProductFactory(name='nitrate')
        cls.product_xmlrpc = ProductFactory(name='xmlrpc')
        cls.components = [
            ComponentFactory(name='application', product=cls.product_nitrate),
            ComponentFactory(name='database', product=cls.product_nitrate),
            ComponentFactory(name='documentation', product=cls.product_xmlrpc),
        ]

    def test_check_component(self):
        cat = product.check_component(None, 'application', self.product_nitrate.pk)
        self.assertEqual(cat['name'], 'application')

    def test_check_component_with_non_exist(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.check_component,
                                     None, "NonExist", self.product_xmlrpc.pk)
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.check_component,
                                     None, 'documentation', 9999)

    def test_check_component_with_no_args(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.check_component, None, 'database', None)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.check_component, None, 'database', [])
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.check_component, None, 'database', {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.check_component, None, 'database', ())

    def test_no_component_queried_with_special_name(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.check_component,
                                     None, None, self.product_nitrate.name)
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.check_component,
                                     None, [], self.product_nitrate.name)
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.check_component,
                                     None, {}, self.product_nitrate.name)
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.check_component,
                                     None, (), self.product_nitrate.name)


class TestCheckProduct(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(name='Nitrate')

    def test_check_product(self):
        cat = product.check_product(None, 'Nitrate')
        self.assertEqual(cat['name'], 'Nitrate')

    def test_check_product_with_non_exist(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.check_product, None, "NonExist")

    def test_check_product_with_no_args(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.check_product, None, None)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.check_product, None, [])
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.check_product, None, {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.check_product, None, ())


class TestFilter(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(name='Nitrate')
        cls.product_xmlrpc = ProductFactory(name='XMLRPC API')

    def test_filter_by_id(self):
        prod = product.filter(None, {"id": self.product.pk})
        self.assertIsNotNone(prod)
        self.assertEqual(prod[0]['name'], 'Nitrate')

    def test_filter_by_name(self):
        prod = product.filter(None, {'name': 'Nitrate'})
        self.assertIsNotNone(prod)
        self.assertEqual(prod[0]['name'], 'Nitrate')

    @unittest.skip('TBD, the API needs change to meet this test.')
    def test_filter_by_non_doc_fields(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.filter, None, {'disallow_new': False})


class TestFilterCategories(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(name='Nitrate')
        cls.categories = [
            TestCaseCategoryFactory(name='auto', product=cls.product),
            TestCaseCategoryFactory(name='manual', product=cls.product),
        ]

    def test_filter_by_product_id(self):
        cat = product.filter_categories(None, {'product': self.product.pk})
        self.assertIsNotNone(cat)

        # PostgreSQL returns data in arbitrary order
        category_names = [c['name'] for c in cat]

        self.assertEqual(3, len(category_names))
        self.assertIn('--default--', category_names)
        self.assertIn('auto', category_names)
        self.assertIn('manual', category_names)

    def test_filter_by_product_name(self):
        cat = product.filter_categories(None, {'name': 'auto'})
        self.assertIsNotNone(cat)
        self.assertEqual(cat[0]['name'], 'auto')


class TestFilterComponents(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(name='StarCraft')
        cls.component = ComponentFactory(name='application', product=cls.product,
                                         initial_owner=None, initial_qa_contact=None)

    def test_filter_by_product_id(self):
        com = product.filter_components(None, {'product': self.product.pk})
        self.assertIsNotNone(com)
        self.assertEqual(com[0]['name'], 'application')

    def test_filter_by_name(self):
        com = product.filter_components(None, {'name': 'application'})
        self.assertIsNotNone(com)
        self.assertEqual(com[0]['name'], 'application')


class TestFilterVersions(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(name='StarCraft')
        cls.version = VersionFactory(value='0.7', product=cls.product)

    def test_filter_by_version_id(self):
        ver = product.filter_versions(None, {'id': self.version.pk})
        self.assertIsNotNone(ver)
        self.assertEqual(ver[0]['value'], "0.7")

    def test_filter_by_product_id(self):
        versions = product.filter_versions(None, {'product_id': self.product.pk})
        self.assertIsInstance(versions, list)
        versions = [version['value'] for version in versions]
        self.assertEqual(2, len(versions))
        self.assertIn('0.7', versions)
        self.assertIn('unspecified', versions)

    def test_filter_by_name(self):
        ver = product.filter_versions(None, {'value': '0.7'})
        self.assertIsNotNone(ver)
        self.assertEqual(ver[0]['value'], "0.7")


class TestGet(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(name='StarCraft')

    def test_get_product(self):
        cat = product.get(None, self.product.pk)
        self.assertEqual(cat['name'], "StarCraft")

    def test_get_product_with_non_exist(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get, None, 9999)

    def test_get_product_with_no_args(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get, None, None)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get, None, [])
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get, None, {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get, None, ())


class TestGetBuilds(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(name='StarCraft')
        cls.builds_count = 3
        cls.builds = [TestBuildFactory(product=cls.product) for i in range(cls.builds_count)]

    def test_get_build_with_id(self):
        builds = product.get_builds(None, self.product.pk)
        self.assertIsNotNone(builds)
        self.assertEqual(len(builds), self.builds_count + 1)
        self.assertEqual('unspecified', builds[0]['name'])

    def test_get_build_with_name(self):
        builds = product.get_builds(None, "StarCraft")
        self.assertIsNotNone(builds)
        self.assertEqual(len(builds), self.builds_count + 1)
        self.assertEqual('unspecified', builds[0]['name'])

    def test_get_build_with_non_exist_prod(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get_builds, None, 9999)
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get_builds, None, "Unknown Product")

    def test_get_build_with_no_args(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_builds, None, None)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_builds, None, [])
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_builds, None, {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_builds, None, ())


class TestGetCases(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.tester = UserFactory(username='great tester')
        cls.product = ProductFactory(name='StarCraft')
        cls.version = VersionFactory(value='0.1', product=cls.product)
        cls.plan = TestPlanFactory(name='Test product.get_cases',
                                   owner=cls.tester, author=cls.tester,
                                   product=cls.product,
                                   product_version=cls.version)
        cls.case_category = TestCaseCategoryFactory(product=cls.product)
        cls.cases_count = 10
        cls.cases = [TestCaseFactory(category=cls.case_category, author=cls.tester,
                                     reviewer=cls.tester, default_tester=None,
                                     plan=[cls.plan])
                     for i in range(cls.cases_count)]

    def test_get_case_with_id(self):
        cases = product.get_cases(None, self.product.pk)
        self.assertIsNotNone(cases)
        self.assertEqual(len(cases), self.cases_count)

    def test_get_case_with_name(self):
        cases = product.get_cases(None, "StarCraft")
        self.assertIsNotNone(cases)
        self.assertEqual(len(cases), self.cases_count)

    def test_get_case_with_non_exist_prod(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get_cases, None, 9999)
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get_cases, None, "Unknown Product")

    def test_get_case_with_no_args(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_cases, None, None)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_cases, None, [])
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_cases, None, {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_cases, None, ())


class TestGetCategories(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(name='StarCraft')
        cls.category_auto = TestCaseCategoryFactory(name='auto', product=cls.product)
        cls.category_manual = TestCaseCategoryFactory(name='manual', product=cls.product)

    def test_get_categories_with_product_id(self):
        cats = product.get_categories(None, self.product.pk)
        self.assertIsNotNone(cats)

        # PostgreSQL returns data in arbitrary order
        category_names = [c['name'] for c in cats]

        self.assertEqual(3, len(category_names))
        self.assertIn('--default--', category_names)
        self.assertIn('auto', category_names)
        self.assertIn('manual', category_names)

    def test_get_categories_with_product_name(self):
        cats = product.get_categories(None, 'StarCraft')
        self.assertIsNotNone(cats)

        # PostgreSQL returns data in arbitrary order
        category_names = [c['name'] for c in cats]

        self.assertEqual(3, len(category_names))
        self.assertIn('--default--', category_names)
        self.assertIn('auto', category_names)
        self.assertIn('manual', category_names)

    def test_get_categories_with_non_exist_prod(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get_categories, None, 9999)
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get_categories, None, "Unknown Product")

    def test_get_categories_with_no_args(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_categories, None, None)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_categories, None, [])
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_categories, None, {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_categories, None, ())


class TestGetCategory(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(name='StarCraft')
        cls.category = TestCaseCategoryFactory(name='manual', product=cls.product)

    def test_get_category(self):
        cat = product.get_category(None, self.category.pk)
        self.assertEqual(cat['name'], 'manual')

    def test_get_category_with_non_exist(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get_category, None, 9999)

    def test_get_category_with_no_args(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_category, None, None)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_category, None, [])
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_category, None, {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_category, None, ())


class TestAddComponent(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.admin = UserFactory()
        cls.staff = UserFactory()
        cls.admin_request = make_http_request(user=cls.admin, user_perm='management.add_component')
        cls.staff_request = make_http_request(user=cls.staff)
        cls.product = ProductFactory()

        # Any added component in tests will be added to this list and then remove them all
        cls.components_to_delete = []

    def test_add_component(self):
        com = product.add_component(self.admin_request, self.product.pk, "application")
        self.components_to_delete.append(com['id'])
        self.assertIsNotNone(com)
        self.assertEqual(com['name'], 'application')
        self.assertEqual(com['initial_owner'], self.admin.username)

    def test_add_component_with_no_perms(self):
        self.assertRaisesXmlrpcFault(FORBIDDEN, product.add_component,
                                     self.staff_request, self.product.pk, "MyComponent")

    def test_add_component_with_non_exist(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.add_component,
                                     self.admin_request, 9999, "MyComponent")


class TestGetComponent(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(name='StarCraft')
        cls.component = ComponentFactory(name='application', product=cls.product)

    def test_get_component(self):
        com = product.get_component(None, self.component.pk)
        self.assertEqual(com['name'], 'application')

    def test_get_component_with_non_exist(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get_component, None, 9999)

    def test_get_component_with_no_args(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_component, None, None)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_component, None, [])
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_component, None, {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_component, None, ())


class TestUpdateComponent(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.admin = UserFactory()
        cls.staff = UserFactory()
        cls.admin_request = make_http_request(user=cls.admin,
                                              user_perm='management.change_component')
        cls.staff_request = make_http_request(user=cls.staff)

        cls.product = ProductFactory(name='StarCraft')
        cls.component = ComponentFactory(name="application", product=cls.product,
                                         initial_owner=None, initial_qa_contact=None)

    def test_update_component(self):
        values = {'name': 'Updated'}
        com = product.update_component(self.admin_request, self.component.pk, values)
        self.assertEqual(com['name'], 'Updated')

    def test_update_component_with_non_exist(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.update_component,
                                     self.admin_request, 1111, {'name': 'new name'})

    def test_update_component_with_no_perms(self):
        self.assertRaisesXmlrpcFault(FORBIDDEN, product.update_component,
                                     self.staff_request, self.component.pk, {})

    def test_update_component_with_special_arg(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.update_component,
                                     self.admin_request, None, {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.update_component,
                                     self.admin_request, [], {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.update_component,
                                     self.admin_request, {}, {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.update_component,
                                     self.admin_request, (), {})

        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.update_component,
                                     self.admin_request, self.component.pk, None)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.update_component,
                                     self.admin_request, self.component.pk, [])
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.update_component,
                                     self.admin_request, self.component.pk, {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.update_component,
                                     self.admin_request, self.component.pk, ())


class TestGetComponents(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(name='StarCraft')
        cls.starcraft_version_0_1 = VersionFactory(value='0.1', product=cls.product)
        cls.components = [
            ComponentFactory(name='application', product=cls.product,
                             initial_owner=None, initial_qa_contact=None),
            ComponentFactory(name='database', product=cls.product,
                             initial_owner=None, initial_qa_contact=None),
            ComponentFactory(name='documentation', product=cls.product,
                             initial_owner=None, initial_qa_contact=None),
        ]

    def test_get_components_with_id(self):
        coms = product.get_components(None, self.product.pk)
        self.assertIsNotNone(coms)
        self.assertEqual(len(coms), 3)
        names = [plan['name'] for plan in coms]
        names.sort()
        expected_names = ['application', 'database', 'documentation']
        self.assertEqual(expected_names, names)

    def test_get_components_with_name(self):
        coms = product.get_components(None, "StarCraft")
        self.assertIsNotNone(coms)
        self.assertEqual(len(coms), 3)
        names = [plan['name'] for plan in coms]
        names.sort()
        expected_names = ['application', 'database', 'documentation']
        self.assertEqual(expected_names, names)

    def test_get_components_with_non_exist_prod(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get_components, None, 9999)
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get_components, None, "Unknown Product")

    def test_get_components_with_no_args(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_components, None, None)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_components, None, [])
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_components, None, {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_components, None, ())


class TestGetEnvironments(XmlrpcAPIBaseTest):

    @unittest.skip('No implemented yet.')
    def test_get_environments(self):
        self.assertRaisesXmlrpcFault(NOT_IMPLEMENTED, product.get_environments, None, None)


class TestGetMilestones(TestCase):

    @unittest.skip('No implemented yet.')
    def test_get_milestones(self):
        self.assertRaisesXmlrpcFault(NOT_IMPLEMENTED, product.get_milestones, None, None)


class TestGetPlans(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(username='jack')
        cls.product_starcraft = ProductFactory(name='StarCraft')
        cls.starcraft_version_0_1 = VersionFactory(value='0.1', product=cls.product_starcraft)
        cls.starcraft_version_0_2 = VersionFactory(value='0.2', product=cls.product_starcraft)
        cls.product_streetfighter = ProductFactory(name='StreetFighter')
        cls.streetfighter_version_0_1 = VersionFactory(value='0.1', product=cls.product_streetfighter)
        cls.plans = [
            TestPlanFactory(name='StarCraft: Init',
                            product=cls.product_starcraft, product_version=cls.starcraft_version_0_1,
                            author=cls.user, owner=cls.user),
            TestPlanFactory(name='StarCraft: Start',
                            product=cls.product_starcraft, product_version=cls.starcraft_version_0_2,
                            author=cls.user, owner=cls.user),
            TestPlanFactory(name='StreetFighter',
                            product=cls.product_streetfighter,
                            product_version=cls.streetfighter_version_0_1,
                            author=cls.user, owner=cls.user),
        ]

    def test_get_plans_with_id(self):
        plans = product.get_plans(None, self.product_starcraft.pk)
        self.assertIsNotNone(plans)
        self.assertEqual(len(plans), 2)
        self.assertEqual(plans[0]['name'], 'StarCraft: Init')
        self.assertEqual(plans[1]['name'], 'StarCraft: Start')

    def test_get_plans_with_name(self):
        plans = product.get_plans(None, 'StarCraft')
        self.assertIsNotNone(plans)
        self.assertEqual(len(plans), 2)
        self.assertEqual(plans[0]['name'], 'StarCraft: Init')
        self.assertEqual(plans[1]['name'], 'StarCraft: Start')

    def test_get_plans_with_non_exist_prod(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get_plans, None, 9999)
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get_plans, None, "Unknown Product")

    def test_get_plans_with_no_args(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_plans, None, None)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_plans, None, [])
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_plans, None, {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_plans, None, ())


class TestGetRuns(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.manager = UserFactory(username='manager')
        cls.product = ProductFactory(name='StarCraft')
        cls.build = TestBuildFactory(product=cls.product)
        cls.runs = [
            TestRunFactory(summary='Test run for StarCraft: Init on Unknown environment',
                           manager=cls.manager, build=cls.build, default_tester=None),
            TestRunFactory(summary='Test run for StarCraft: second one',
                           manager=cls.manager, build=cls.build, default_tester=None),
        ]

    def test_get_runs_with_id(self):
        runs = product.get_runs(None, self.product.pk)
        self.assertIsNotNone(runs)
        self.assertEqual(len(runs), 2)
        self.assertEqual(runs[0]['summary'],
                         'Test run for StarCraft: Init on Unknown environment')
        self.assertEqual(runs[1]['summary'],
                         'Test run for StarCraft: second one')

    def test_get_runs_with_name(self):
        runs = product.get_runs(None, 'StarCraft')
        self.assertIsNotNone(runs)
        self.assertEqual(len(runs), 2)
        self.assertEqual(runs[0]['summary'],
                         'Test run for StarCraft: Init on Unknown environment')
        self.assertEqual(runs[1]['summary'],
                         'Test run for StarCraft: second one')

    def test_get_runs_with_non_exist_prod(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get_runs, None, 9999)
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get_runs, None, "Unknown Product")

    def test_get_runs_with_no_args(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_runs, None, None)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_runs, None, [])
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_runs, None, {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_runs, None, ())


class TestGetTag(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.tag = TestTagFactory(name='QWER')

    def test_get_tag(self):
        tag = product.get_tag(None, self.tag.pk)
        self.assertEqual(tag['name'], "QWER")

        tag = product.get_tag(None, str(self.tag.pk))
        self.assertEqual(tag['name'], "QWER")

    def test_get_tag_with_non_exist(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get_tag, None, 9999)

    def test_get_tag_with_no_args(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_tag, None, None)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_tag, None, [])
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_tag, None, {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_tag, None, ())


class TestAddVersion(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.product_name = 'StarCraft'
        cls.product = ProductFactory(name=cls.product_name)
        cls.admin = UserFactory(username='tcr_admin', email='tcr_admin@example.com')
        cls.staff = UserFactory(username='tcr_staff', email='tcr_staff@example.com')
        cls.admin_request = make_http_request(user=cls.admin, user_perm='management.add_version')
        cls.staff_request = make_http_request(user=cls.staff)

    def test_add_version_with_no_args(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.add_version, self.admin_request, None)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.add_version, self.admin_request, [])
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.add_version, self.admin_request, {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.add_version, self.admin_request, ())

    def test_add_version_with_product_id(self):
        prod = product.add_version(self.admin_request, {
            "product": self.product.pk,
            "value": "New Version 1"
        })
        self.assertEqual(prod['value'], "New Version 1")
        self.assertEqual(prod['product_id'], self.product.pk)

    def test_add_version_with_product_name(self):
        new_version = 'New Version 2'
        prod = product.add_version(self.admin_request, {
            'product': self.product_name,
            'value': new_version,
        })
        self.assertEqual(prod['value'], new_version)
        self.assertEqual(prod['product_id'], self.product.pk)

    def test_add_version_with_non_exist_prod(self):
        non_existing_product_pk = 111111
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.add_version,
                                     self.admin_request,
                                     {"product": non_existing_product_pk, "value": "0.1"})

    def test_add_version_with_missing_argument(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.add_version,
                                     self.admin_request, {"product": self.product.pk})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.add_version,
                                     self.admin_request, {"value": "0.1"})

    def test_add_version_with_extra_unrecognized_field(self):
        new_version = product.add_version(self.admin_request, {
            'product': self.product.pk,
            'value': 'New version',
            'data': 'Extra value that is not expected',
        })
        self.assertEqual(self.product.pk, new_version['product_id'])
        self.assertEqual(self.product.name, new_version['product'])
        self.assertEqual('New version', new_version['value'])

    def test_add_version_with_no_perms(self):
        self.assertRaisesXmlrpcFault(FORBIDDEN, product.add_version, self.staff_request, {})


class TestGetVersions(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.product_name = 'StarCraft'
        cls.versions = ['0.6', '0.7', '0.8', '0.9', '1.0']

        cls.product = ProductFactory(name=cls.product_name)
        cls.product_versions = [VersionFactory(product=cls.product, value=version)
                                for version in cls.versions]

    def test_get_versions_with_id(self):
        prod = product.get_versions(None, self.product.pk)
        self.assertIsNotNone(prod)
        versions = [item['value'] for item in prod]
        versions.sort()
        self.assertEqual(self.versions + ['unspecified'], versions)

    def test_get_versions_with_name(self):
        prod = product.get_versions(None, self.product_name)
        self.assertIsNotNone(prod)
        versions = [item['value'] for item in prod]
        versions.sort()
        self.assertEqual(self.versions + ['unspecified'], versions)

    def test_get_version_with_no_args(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_versions, None, None)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_versions, None, [])
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_versions, None, {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_versions, None, ())

    def test_get_version_with_non_exist_prod(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get_versions, None, 99999)
        self.assertRaisesXmlrpcFault(NOT_FOUND, product.get_versions, None, "Missing Product")

    def test_get_version_with_bad_args(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_versions, None, True)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_versions, None, False)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_versions, None, '')
        self.assertRaisesXmlrpcFault(BAD_REQUEST, product.get_versions, None, object)
