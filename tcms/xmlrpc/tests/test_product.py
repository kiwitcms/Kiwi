# -*- coding: utf-8 -*-

from xmlrpc.client import ProtocolError
from xmlrpc.client import Fault as XmlRPCFault

from tcms.tests.factories import ComponentFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestCaseCategoryFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestCheckComponent(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestCheckComponent, self)._fixture_setup()

        self.product_nitrate = ProductFactory(name='nitrate')
        self.product_xmlrpc = ProductFactory(name='xmlrpc')
        self.components = [
            ComponentFactory(name='application', product=self.product_nitrate),
            ComponentFactory(name='database', product=self.product_nitrate),
            ComponentFactory(name='documentation', product=self.product_xmlrpc),
        ]

    def test_check_component(self):
        cat = self.rpc_client.Product.check_component('application', self.product_nitrate.pk)
        self.assertEqual(cat['name'], 'application')

    def test_check_component_search_by_product_name(self):
        cat = self.rpc_client.Product.check_component('documentation', self.product_xmlrpc.pk)
        self.assertEqual(cat['name'], 'documentation')

        # there's no component named documentation for product Nitrate
        with self.assertRaisesRegex(XmlRPCFault, 'Component matching query does not exist'):
            self.rpc_client.Product.check_component('documentation', self.product_nitrate.pk)

    def test_check_component_with_non_exist(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Component matching query does not exist'):
            self.rpc_client.Product.check_component("NonExist", self.product_xmlrpc.pk)

        with self.assertRaisesRegex(XmlRPCFault, 'Product matching query does not exist'):
            self.rpc_client.Product.check_component('documentation', -9999)


class TestFilter(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestFilter, self)._fixture_setup()

        self.product = ProductFactory(name='Nitrate')
        self.product_xmlrpc = ProductFactory(name='XMLRPC API')

    def test_filter_by_id(self):
        prod = self.rpc_client.Product.filter({"id": self.product.pk})
        self.assertIsNotNone(prod)
        self.assertEqual(prod[0]['name'], 'Nitrate')

    def test_filter_by_name(self):
        prod = self.rpc_client.Product.filter({'name': 'Nitrate'})
        self.assertIsNotNone(prod)
        self.assertEqual(prod[0]['name'], 'Nitrate')

    def test_filter_non_existing(self):
        found = self.rpc_client.Product.filter({'name': "Non Existing"})
        self.assertEqual(0, len(found))


class TestFilterComponents(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestFilterComponents, self)._fixture_setup()

        self.product = ProductFactory(name='StarCraft')
        self.component = ComponentFactory(name='application', product=self.product,
                                          initial_owner=None, initial_qa_contact=None)

    def test_filter_by_product_id(self):
        com = self.rpc_client.Product.filter_components({'product': self.product.pk})
        self.assertIsNotNone(com)
        self.assertEqual(com[0]['name'], 'application')

    def test_filter_by_name(self):
        com = self.rpc_client.Product.filter_components({'name': 'application'})
        self.assertIsNotNone(com)
        self.assertEqual(com[0]['name'], 'application')


class TestFilterVersions(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestFilterVersions, self)._fixture_setup()

        self.product = ProductFactory(name='StarCraft')
        self.version = VersionFactory(value='0.7', product=self.product)

    def test_filter_by_version_id(self):
        ver = self.rpc_client.Product.filter_versions({'id': self.version.pk})
        self.assertIsNotNone(ver)
        self.assertEqual(ver[0]['value'], "0.7")

    def test_filter_by_product_id(self):
        versions = self.rpc_client.Product.filter_versions({'product_id': self.product.pk})
        self.assertIsInstance(versions, list)
        versions = [version['value'] for version in versions]
        self.assertEqual(2, len(versions))
        self.assertIn('0.7', versions)
        self.assertIn('unspecified', versions)

    def test_filter_by_name(self):
        ver = self.rpc_client.Product.filter_versions({'value': '0.7'})
        self.assertIsNotNone(ver)
        self.assertEqual(ver[0]['value'], "0.7")


class TestGetCases(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestGetCases, self)._fixture_setup()

        self.tester = UserFactory(username='great tester')
        self.product = ProductFactory(name='StarCraft')
        self.version = VersionFactory(value='0.1', product=self.product)
        self.plan = TestPlanFactory(name='Test product.get_cases',
                                    owner=self.tester, author=self.tester,
                                    product=self.product,
                                    product_version=self.version)
        self.case_category = TestCaseCategoryFactory(product=self.product)
        self.cases_count = 10
        self.cases = [TestCaseFactory(category=self.case_category, author=self.tester,
                                      reviewer=self.tester, default_tester=None,
                                      plan=[self.plan])
                      for i in range(self.cases_count)]

    def test_get_case_with_id(self):
        cases = self.rpc_client.Product.get_cases(self.product.pk)
        self.assertIsNotNone(cases)
        self.assertEqual(len(cases), self.cases_count)

    def test_get_case_with_name(self):
        cases = self.rpc_client.Product.get_cases("StarCraft")
        self.assertIsNotNone(cases)
        self.assertEqual(len(cases), self.cases_count)


class TestAddComponent(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestAddComponent, self)._fixture_setup()

        self.product = ProductFactory()

        # Any added component in tests will be added to this list and then remove them all
        self.components_to_delete = []

    def test_add_component(self):
        com = self.rpc_client.Product.add_component(self.product.pk, "application")
        self.components_to_delete.append(com['id'])
        self.assertIsNotNone(com)
        self.assertEqual(com['name'], 'application')
        self.assertEqual(com['initial_owner'], self.api_user.username)

    def test_add_component_with_no_perms(self):
        self.rpc_client.Auth.logout()
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.Product.add_component(self.product.pk, "MyComponent")


class TestGetComponent(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestGetComponent, self)._fixture_setup()

        self.product = ProductFactory(name='StarCraft')
        self.component = ComponentFactory(name='application', product=self.product)

    def test_get_component(self):
        com = self.rpc_client.Product.get_component(self.component.pk)
        self.assertEqual(com['name'], 'application')

    def test_get_component_with_non_exist(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Component matching query does not exist'):
            self.rpc_client.Product.get_component(-99)


class TestUpdateComponent(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestUpdateComponent, self)._fixture_setup()

        self.product = ProductFactory(name='StarCraft')
        self.component = ComponentFactory(name="application", product=self.product,
                                          initial_owner=None, initial_qa_contact=None)

    def test_update_component(self):
        values = {'name': 'Updated'}
        com = self.rpc_client.Product.update_component(self.component.pk, values)
        self.assertEqual(com['name'], 'Updated')

    def test_update_component_with_non_exist(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Component matching query does not exist'):
            self.rpc_client.Product.update_component(-99, {'name': 'new name'})

    def test_update_component_with_no_perms(self):
        self.rpc_client.Auth.logout()
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.Product.update_component(self.component.pk, {})


class TestAddVersion(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestAddVersion, self)._fixture_setup()

        self.product_name = 'StarCraft'
        self.product = ProductFactory(name=self.product_name)

    def test_add_version_with_product_id(self):
        prod = self.rpc_client.Product.add_version({
            "product": self.product.pk,
            "value": "New Version 1"
        })
        self.assertEqual(prod['value'], "New Version 1")
        self.assertEqual(prod['product_id'], self.product.pk)

    def test_add_version_with_product_name(self):
        new_version = 'New Version 2'
        prod = self.rpc_client.Product.add_version({
            'product': self.product_name,
            'value': new_version,
        })
        self.assertEqual(prod['value'], new_version)
        self.assertEqual(prod['product_id'], self.product.pk)

    def test_add_version_with_non_exist_prod(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Product matching query does not exist'):
            self.rpc_client.Product.add_version({
                "product": -9,
                "value": "0.1"
            })

    def test_add_version_with_missing_argument(self):
        with self.assertRaisesRegex(XmlRPCFault, "Internal error:.*value.*This field is required"):
            self.rpc_client.Product.add_version({"product": self.product.pk})

        with self.assertRaisesRegex(XmlRPCFault, 'No product given'):
            self.rpc_client.Product.add_version({"value": "0.1"})

    def test_add_version_with_extra_unrecognized_field(self):
        new_version = self.rpc_client.Product.add_version({
            'product': self.product.pk,
            'value': 'New version',
            'extra-data-field': 'Extra value that is not expected',
        })
        self.assertEqual(self.product.pk, new_version['product_id'])
        self.assertEqual(self.product.name, new_version['product'])
        self.assertEqual('New version', new_version['value'])

    def test_add_version_with_no_perms(self):
        self.rpc_client.Auth.logout()
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.Product.add_version({})
