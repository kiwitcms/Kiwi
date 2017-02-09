# -*- coding: utf-8 -*-

import unittest

from xmlrpclib import Fault

from django.test import TestCase

from tcms.xmlrpc.api import product
from tcms.xmlrpc.tests.utils import make_http_request

from tcms.management.models import Component
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


class AssertMessage(object):
    NOT_VALIDATE_ARGS = "Missing validations for args."
    NOT_VALIDATE_REQUIRED_ARGS = "Missing validations for required args."
    NOT_VALIDATE_ILLEGAL_ARGS = "Missing validations for illegal args."
    NOT_VALIDATE_FOREIGN_KEY = "Missing validations for foreign key."
    NOT_VALIDATE_LENGTH = "Missing validations for length of value."
    NOT_VALIDATE_URL_FORMAT = "Missing validations for URL format."

    SHOULD_BE_400 = "Error code should be 400."
    SHOULD_BE_409 = "Error code should be 409."
    SHOULD_BE_500 = "Error code should be 500."
    SHOULD_BE_403 = "Error code should be 403."
    SHOULD_BE_401 = "Error code should be 401."
    SHOULD_BE_404 = "Error code should be 404."
    SHOULD_BE_501 = "Error code should be 501."
    SHOULD_BE_1 = "Error code should be 1."

    UNEXCEPT_ERROR = "Unexcept error occurs."
    NEED_ENCODE_UTF8 = "Need to encode with utf8."

    NOT_IMPLEMENT_FUNC = "Not implement yet."
    XMLRPC_INTERNAL_ERROR = "xmlrpc library error."
    NOT_VALIDATE_PERMS = "Missing validations for user perms."


class TestCheckCategory(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.product_nitrate = ProductFactory(name='nitrate')
        cls.product_xmlrpc = ProductFactory(name='xmlrpc')
        cls.case_categories = [
            TestCaseCategoryFactory(name='auto', product=cls.product_nitrate),
            TestCaseCategoryFactory(name='manual', product=cls.product_nitrate),
            TestCaseCategoryFactory(name='pending', product=cls.product_xmlrpc),
        ]

    @classmethod
    def tearDownClass(cls):
        [category.delete() for category in cls.case_categories]
        cls.product_xmlrpc.delete()
        cls.product_xmlrpc.classification.delete()
        cls.product_nitrate.delete()
        cls.product_nitrate.classification.delete()

    def test_check_category(self):
        try:
            cat = product.check_category(None, 'manual', self.product_nitrate.pk)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(cat['name'], 'manual')

    def test_check_category_with_non_exist_category(self):
        try:
            product.check_category(None, "NonExist", self.product_nitrate.pk)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

        try:
            product.check_category(None, "--default--", 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

    def test_check_category_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.check_category(None, "--default--", arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_no_category_queried_by_special_name(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.check_category(None, arg, self.product_nitrate.name)
            except Fault as f:
                self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestCheckComponent(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.product_nitrate = ProductFactory(name='nitrate')
        cls.product_xmlrpc = ProductFactory(name='xmlrpc')
        cls.components = [
            ComponentFactory(name='application', product=cls.product_nitrate),
            ComponentFactory(name='database', product=cls.product_nitrate),
            ComponentFactory(name='documentation', product=cls.product_xmlrpc),
        ]

    @classmethod
    def tearDownClass(cls):
        for component in cls.components:
            component.delete()
        cls.product_nitrate.delete()
        cls.product_nitrate.classification.delete()
        cls.product_xmlrpc.delete()
        cls.product_xmlrpc.classification.delete()

    def test_check_component(self):
        try:
            cat = product.check_component(None, 'application', self.product_nitrate.pk)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(cat['name'], 'application')

    def test_check_component_with_non_exist(self):
        try:
            product.check_component(None, "NonExist", self.product_xmlrpc.pk)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

        try:
            product.check_component(None, 'documentation', 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

    def test_check_component_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.check_component(None, 'database', arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_no_component_queried_with_special_name(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.check_component(None, arg, self.product_nitrate.name)
            except Fault as f:
                self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestCheckProduct(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.product = ProductFactory(name='Nitrate')

    @classmethod
    def tearDownClass(cls):
        cls.product.delete()
        cls.product.classification.delete()

    def test_check_product(self):
        try:
            cat = product.check_product(None, 'Nitrate')
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(cat['name'], 'Nitrate')

    def test_check_product_with_non_exist(self):
        try:
            product.check_product(None, "NonExist")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

    def test_check_product_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.check_product(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestFilter(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.product = ProductFactory(name='Nitrate')
        cls.product_xmlrpc = ProductFactory(name='XMLRPC API')

    @classmethod
    def tearDownClass(cls):
        cls.product.delete()
        cls.product.classification.delete()
        cls.product_xmlrpc.delete()
        cls.product_xmlrpc.classification.delete()

    def test_filter_by_id(self):
        try:
            prod = product.filter(None, {"id": self.product.pk})
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(prod)
            self.assertEqual(prod[0]['name'], 'Nitrate')

    def test_filter_by_name(self):
        try:
            prod = product.filter(None, {'name': 'Nitrate'})
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(prod)
            self.assertEqual(prod[0]['name'], 'Nitrate')

    @unittest.skip('TBD, the API needs change to meet this test.')
    def test_filter_by_non_doc_fields(self):
        try:
            product.filter(None, {'disallow_new': False})
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestFilterCategories(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.product = ProductFactory(name='Nitrate')
        cls.categories = [
            TestCaseCategoryFactory(name='auto', product=cls.product),
            TestCaseCategoryFactory(name='manual', product=cls.product),
        ]

    @classmethod
    def tearDownClass(cls):
        for category in cls.categories:
            category.delete()
        cls.product.delete()
        cls.product.classification.delete()

    def test_filter_by_product_id(self):
        try:
            cat = product.filter_categories(None, {'product': self.product.pk})
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(cat)
            self.assertEqual(cat[0]['name'], '--default--')
            self.assertEqual(cat[1]['name'], 'auto')
            self.assertEqual(cat[2]['name'], 'manual')

    def test_filter_by_product_name(self):
        try:
            cat = product.filter_categories(None, {'name': 'auto'})
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(cat)
            self.assertEqual(cat[0]['name'], 'auto')


class TestFilterComponents(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.product = ProductFactory(name='StarCraft')
        cls.component = ComponentFactory(name='application', product=cls.product,
                                         initial_owner=None, initial_qa_contact=None)

    @classmethod
    def tearDownClass(cls):
        cls.component.delete()
        cls.product.delete()
        cls.product.classification.delete()

    def test_filter_by_product_id(self):
        try:
            com = product.filter_components(None, {'product': self.product.pk})
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(com)
            self.assertEqual(com[0]['name'], 'application')

    def test_filter_by_name(self):
        try:
            com = product.filter_components(None, {'name': 'application'})
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(com)
            self.assertEqual(com[0]['name'], 'application')


class TestFilterVersions(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.product = ProductFactory(name='StarCraft')
        cls.version = VersionFactory(value='0.7', product=cls.product)

    @classmethod
    def tearDownClass(cls):
        cls.version.delete()
        cls.product.delete()
        cls.product.classification.delete()

    def test_filter_by_id(self):
        try:
            ver = product.filter_versions(None, {'id': self.product.pk})
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(ver)
            self.assertEqual(ver[0]['value'], "unspecified")

    def test_filter_by_name(self):
        try:
            ver = product.filter_versions(None, {'value': '0.7'})
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(ver)
            self.assertEqual(ver[0]['value'], "0.7")


class TestGet(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.product = ProductFactory(name='StarCraft')

    @classmethod
    def tearDownClass(cls):
        cls.product.delete()
        cls.product.classification.delete()

    def test_get_product(self):
        try:
            cat = product.get(None, self.product.pk)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(cat['name'], "StarCraft")

    def test_get_product_with_non_exist(self):
        try:
            product.get(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

    def test_get_product_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestGetBuilds(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.product = ProductFactory(name='StarCraft')
        cls.builds_count = 3
        cls.builds = [TestBuildFactory(product=cls.product) for i in range(cls.builds_count)]

    @classmethod
    def tearDownClass(cls):
        for build in cls.builds:
            build.delete()
        cls.product.delete()
        cls.product.classification.delete()

    def test_get_build_with_id(self):
        try:
            builds = product.get_builds(None, self.product.pk)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(builds)
            self.assertEqual(len(builds), self.builds_count + 1)
            self.assertEqual('unspecified', builds[0]['name'])

    def test_get_build_with_name(self):
        try:
            builds = product.get_builds(None, "StarCraft")
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(builds)
            self.assertEqual(len(builds), self.builds_count + 1)
            self.assertEqual('unspecified', builds[0]['name'])

    def test_get_build_with_non_exist_prod(self):
        try:
            product.get_builds(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            product.get_builds(None, "Unknown Product")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_build_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_builds(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestGetCases(TestCase):

    @classmethod
    def setUpClass(cls):
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

    @classmethod
    def tearDownClass(cls):
        for case in cls.cases:
            case.delete()
        cls.plan.delete()
        cls.version.delete()
        cls.product.delete()
        cls.product.classification.delete()
        cls.tester.delete()

    def test_get_case_with_id(self):
        try:
            cases = product.get_cases(None, self.product.pk)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(cases)
            self.assertEqual(len(cases), self.cases_count)

    def test_get_case_with_name(self):
        try:
            cases = product.get_cases(None, "StarCraft")
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(cases)
            self.assertEqual(len(cases), self.cases_count)

    def test_get_case_with_non_exist_prod(self):
        try:
            product.get_cases(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            product.get_cases(None, "Unknown Product")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_case_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_cases(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestGetCategories(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.product = ProductFactory(name='StarCraft')
        cls.category_auto = TestCaseCategoryFactory(name='auto', product=cls.product)
        cls.category_manual = TestCaseCategoryFactory(name='manual', product=cls.product)

    @classmethod
    def tearDownClass(cls):
        cls.category_auto.delete()
        cls.category_manual.delete()
        cls.product.delete()
        cls.product.classification.delete()

    def test_get_categories_with_product_id(self):
        try:
            cats = product.get_categories(None, self.product.pk)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(cats)
            self.assertEqual(len(cats), 3)
            self.assertTrue(cats[0]['name'], '--default--')
            self.assertTrue(cats[1]['name'], 'auto')
            self.assertTrue(cats[2]['name'], 'manual')

    def test_get_categories_with_product_name(self):
        try:
            cats = product.get_categories(None, 'StarCraft')
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(cats)
            self.assertEqual(len(cats), 3)
            self.assertEqual(cats[0]['name'], '--default--')
            self.assertEqual(cats[1]['name'], 'auto')
            self.assertEqual(cats[2]['name'], 'manual')

    def test_get_categories_with_non_exist_prod(self):
        try:
            product.get_categories(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            product.get_categories(None, "Unknown Product")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_categories_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_categories(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestGetCategory(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.product = ProductFactory(name='StarCraft')
        cls.category = TestCaseCategoryFactory(name='manual', product=cls.product)

    @classmethod
    def tearDownClass(cls):
        cls.category.delete()
        cls.product.delete()
        cls.product.classification.delete()

    def test_get_category(self):
        try:
            cat = product.get_category(None, self.category.pk)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(cat['name'], 'manual')

    def test_get_category_with_non_exist(self):
        try:
            product.get_category(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

    def test_get_category_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_category(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestAddComponent(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.admin = UserFactory()
        cls.staff = UserFactory()
        cls.admin_request = make_http_request(user=cls.admin, user_perm='management.add_component')
        cls.staff_request = make_http_request(user=cls.staff)
        cls.product = ProductFactory()

        # Any added component in tests will be added to this list and then remove them all
        cls.components_to_delete = []

    @classmethod
    def tearDownClass(cls):
        Component.objects.filter(pk__in=cls.components_to_delete).delete()
        cls.staff.delete()
        cls.admin.delete()
        cls.product.delete()
        cls.product.classification.delete()

    def test_add_component(self):
        try:
            com = product.add_component(self.admin_request, self.product.pk, "application")
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.components_to_delete.append(com['id'])
            self.assertIsNotNone(com)
            self.assertEqual(com['name'], 'application')
            self.assertEqual(com['initial_owner'], self.admin.username)

    def test_add_component_with_no_perms(self):
        try:
            product.add_component(self.staff_request, self.product.pk, "MyComponent")
        except Fault as f:
            self.assertEqual(f.faultCode, 403, AssertMessage.SHOULD_BE_403)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_PERMS)

    def test_add_component_with_non_exist(self):
        try:
            product.add_component(self.admin_request, 9999, "MyComponent")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_PERMS)


class TestGetComponent(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.product = ProductFactory(name='StarCraft')
        cls.component = ComponentFactory(name='application', product=cls.product)

    @classmethod
    def tearDownClass(cls):
        cls.component.delete()
        cls.product.delete()
        cls.product.classification.delete()

    def test_get_component(self):
        try:
            com = product.get_component(None, self.component.pk)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(com['name'], 'application')

    def test_get_component_with_non_exist(self):
        try:
            product.get_component(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

    def test_get_component_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_component(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestUpdateComponent(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.admin = UserFactory()
        cls.staff = UserFactory()
        cls.admin_request = make_http_request(user=cls.admin,
                                              user_perm='management.change_component')
        cls.staff_request = make_http_request(user=cls.staff)

        cls.product = ProductFactory(name='StarCraft')
        cls.component = ComponentFactory(name="application", product=cls.product,
                                         initial_owner=None, initial_qa_contact=None)

    @classmethod
    def tearDownClass(cls):
        cls.component.delete()
        cls.product.delete()
        cls.product.classification.delete()
        cls.staff.delete()
        cls.admin.delete()

    def test_update_component(self):
        try:
            values = {'name': 'Updated'}
            com = product.update_component(self.admin_request, self.component.pk, values)
        except Fault:
            raise
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(com['name'], 'Updated')

    def test_update_component_with_non_exist(self):
        try:
            product.update_component(self.admin_request, 1111, {'name': 'new name'})
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_component_with_no_perms(self):
        try:
            product.update_component(self.staff_request, self.component.pk, {})
        except Fault as f:
            self.assertEqual(f.faultCode, 403, AssertMessage.SHOULD_BE_403)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_PERMS)

    def test_update_component_with_special_arg(self):
        bad_args = (None, [], {}, ())

        for arg in bad_args:
            try:
                product.update_component(self.admin_request, arg, {})
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        for arg in bad_args:
            try:
                product.update_component(self.admin_request, self.component.pk, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestGetComponents(TestCase):

    @classmethod
    def setUpClass(cls):
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

    @classmethod
    def tearDownClass(cls):
        [component.delete() for component in cls.components]
        cls.starcraft_version_0_1.delete()
        cls.product.delete()
        cls.product.classification.delete()

    def test_get_components_with_id(self):
        try:
            coms = product.get_components(None, self.product.pk)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(coms)
            self.assertEqual(len(coms), 3)
            names = [plan['name'] for plan in coms]
            names.sort()
            expected_names = ['application', 'database', 'documentation']
            self.assertEqual(expected_names, names)

    def test_get_components_with_name(self):
        try:
            coms = product.get_components(None, "StarCraft")
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(coms)
            self.assertEqual(len(coms), 3)
            names = [plan['name'] for plan in coms]
            names.sort()
            expected_names = ['application', 'database', 'documentation']
            self.assertEqual(expected_names, names)

    def test_get_components_with_non_exist_prod(self):
        try:
            product.get_components(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            product.get_components(None, "Unknown Product")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_components_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_components(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestGetEnvironments(TestCase):

    @unittest.skip('No implemented yet.')
    def test_get_environments(self):
        try:
            product.get_environments(None, None)
        except Fault as f:
            self.assertEqual(f.faultCode, 501, AssertMessage.SHOULD_BE_501)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)


class TestGetMilestones(TestCase):

    @unittest.skip('No implemented yet.')
    def test_get_milestones(self):
        try:
            product.get_milestones(None, None)
        except Fault as f:
            self.assertEqual(f.faultCode, 501, AssertMessage.SHOULD_BE_501)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)


class TestGetPlans(TestCase):

    @classmethod
    def setUpClass(cls):
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

    @classmethod
    def tearDownClass(cls):
        [plan.delete() for plan in cls.plans]
        cls.starcraft_version_0_1.delete()
        cls.starcraft_version_0_2.delete()
        cls.streetfighter_version_0_1.delete()
        cls.product_starcraft.delete()
        cls.product_starcraft.classification.delete()
        cls.product_streetfighter.delete()
        cls.product_streetfighter.classification.delete()
        cls.user.delete()

    def test_get_plans_with_id(self):
        try:
            plans = product.get_plans(None, self.product_starcraft.pk)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(plans)
            self.assertEqual(len(plans), 2)
            self.assertEqual(plans[0]['name'], 'StarCraft: Init')
            self.assertEqual(plans[1]['name'], 'StarCraft: Start')

    def test_get_plans_with_name(self):
        try:
            plans = product.get_plans(None, 'StarCraft')
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(plans)
            self.assertEqual(len(plans), 2)
            self.assertEqual(plans[0]['name'], 'StarCraft: Init')
            self.assertEqual(plans[1]['name'], 'StarCraft: Start')

    def test_get_plans_with_non_exist_prod(self):
        try:
            product.get_plans(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            product.get_plans(None, "Unknown Product")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_plans_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_plans(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestGetRuns(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.manager = UserFactory(username='manager')
        cls.product = ProductFactory(name='StarCraft')
        cls.build = TestBuildFactory(product=cls.product)
        cls.runs = [
            TestRunFactory(summary='Test run for StarCraft: Init on Unknown environment',
                           manager=cls.manager, build=cls.build, default_tester=None),
            TestRunFactory(summary='Test run for StarCraft: second one',
                           manager=cls.manager, build=cls.build, default_tester=None),
        ]

    @classmethod
    def tearDownClass(cls):
        [run.delete() for run in cls.runs]
        cls.build.delete()
        cls.product.delete()
        cls.product.classification.delete()
        cls.manager.delete()

    def test_get_runs_with_id(self):
        try:
            runs = product.get_runs(None, self.product.pk)
        except Fault:
            raise
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(runs)
            self.assertEqual(len(runs), 2)
            self.assertEqual(runs[0]['summary'],
                             'Test run for StarCraft: Init on Unknown environment')
            self.assertEqual(runs[1]['summary'],
                             'Test run for StarCraft: second one')

    def test_get_runs_with_name(self):
        try:
            runs = product.get_runs(None, 'StarCraft')
        except Fault:
            raise
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(runs)
            self.assertEqual(len(runs), 2)
            self.assertEqual(runs[0]['summary'],
                             'Test run for StarCraft: Init on Unknown environment')
            self.assertEqual(runs[1]['summary'],
                             'Test run for StarCraft: second one')

    def test_get_runs_with_non_exist_prod(self):
        try:
            product.get_runs(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            product.get_runs(None, "Unknown Product")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_runs_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_runs(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestGetTag(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tag = TestTagFactory(name='QWER')

    @classmethod
    def tearDownClass(cls):
        cls.tag.delete()

    def test_get_tag(self):
        try:
            tag = product.get_tag(None, self.tag.pk)
        except Fault:
            raise
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(tag['name'], "QWER")

        try:
            tag = product.get_tag(None, str(self.tag.pk))
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(tag['name'], "QWER")

    def test_get_tag_with_non_exist(self):
        try:
            product.get_tag(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

    def test_get_tag_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_tag(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestAddVersion(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.product_name = 'StarCraft'
        cls.product = ProductFactory(name=cls.product_name)
        cls.admin = UserFactory(username='tcr_admin', email='tcr_admin@example.com')
        cls.staff = UserFactory(username='tcr_staff', email='tcr_staff@example.com')
        cls.admin_request = make_http_request(user=cls.admin, user_perm='management.add_version')
        cls.staff_request = make_http_request(user=cls.staff)

    @classmethod
    def tearDownClass(cls):
        cls.product.delete()
        cls.product.classification.delete()
        cls.admin.delete()
        cls.staff.delete()

    def test_add_version_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.add_version(self.admin_request, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_add_version_with_product_id(self):
        try:
            prod = product.add_version(self.admin_request, {
                "product": self.product.pk,
                "value": "New Version 1"
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(prod['value'], "New Version 1")
            self.assertEqual(prod['product_id'], self.product.pk)

    def test_add_version_with_product_name(self):
        new_version = 'New Version 2'
        try:
            prod = product.add_version(self.admin_request, {
                'product': self.product_name,
                'value': new_version,
            })
        except Fault:
            raise
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(prod['value'], new_version)
            self.assertEqual(prod['product_id'], self.product.pk)

    def test_add_version_with_non_exist_prod(self):
        non_existing_product_pk = 111111
        try:
            product.add_version(self.admin_request, {
                "product": non_existing_product_pk,
                "value": "0.1",
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_add_version_with_missing_argument(self):
        try:
            product.add_version(self.admin_request, {"product": self.product.pk})
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            product.add_version(self.admin_request, {"value": "0.1"})
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_add_version_with_extra_unrecognized_field(self):
        try:
            new_version = product.add_version(self.admin_request, {
                'product': self.product.pk,
                'value': 'New version',
                'data': 'Extra value that is not expected',
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.assertEqual(self.product.pk, new_version['product_id'])
            self.assertEqual(self.product.name, new_version['product'])
            self.assertEqual('New version', new_version['value'])

    def test_add_version_with_no_perms(self):
        try:
            product.add_version(self.staff_request, {})
        except Fault as f:
            self.assertEqual(f.faultCode, 403, AssertMessage.SHOULD_BE_403)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_PERMS)


class TestGetVersions(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.product_name = 'StarCraft'
        cls.versions = ['0.6', '0.7', '0.8', '0.9', '1.0']

        cls.product = ProductFactory(name=cls.product_name)
        cls.product_versions = [VersionFactory(product=cls.product, value=version)
                                for version in cls.versions]

    @classmethod
    def tearDownClass(cls):
        [version.delete() for version in cls.product_versions]
        cls.product.delete()
        cls.product.classification.delete()

    def test_get_versions_with_id(self):
        try:
            prod = product.get_versions(None, self.product.pk)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(prod)
            versions = [item['value'] for item in prod]
            versions.sort()
            self.assertEqual(self.versions + ['unspecified'], versions)

    def test_get_versions_with_name(self):
        try:
            prod = product.get_versions(None, self.product_name)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(prod)
            versions = [item['value'] for item in prod]
            versions.sort()
            self.assertEqual(self.versions + ['unspecified'], versions)

    def test_get_version_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_versions(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_version_with_non_exist_prod(self):
        try:
            product.get_versions(None, 99999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            product.get_versions(None, "Missing Product")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_version_with_bad_args(self):
        bad_args = (True, False, '', object)
        for arg in bad_args:
            try:
                product.get_versions(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)
