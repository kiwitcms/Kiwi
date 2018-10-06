# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, invalid-name

from xmlrpc.client import ProtocolError
from xmlrpc.client import Fault as XmlRPCFault

from tcms.tests.factories import ComponentFactory
from tcms.tests.factories import ProductFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestFilterComponents(XmlrpcAPIBaseTest):
    def _fixture_setup(self):
        super(TestFilterComponents, self)._fixture_setup()

        self.product = ProductFactory(name='StarCraft')
        self.component = ComponentFactory(name='application', product=self.product,
                                          initial_owner=None, initial_qa_contact=None)

    def test_filter_by_product_id(self):
        com = self.rpc_client.exec.Component.filter({'product': self.product.pk})
        self.assertIsNotNone(com)
        self.assertEqual(com[0]['name'], 'application')

    def test_filter_by_name(self):
        com = self.rpc_client.exec.Component.filter({'name': 'application'})
        self.assertIsNotNone(com)
        self.assertEqual(com[0]['name'], 'application')

    def test_filter_non_existing(self):
        found = self.rpc_client.exec.Component.filter({'name': 'documentation'})
        self.assertEqual(0, len(found))


class TestCreateComponent(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestCreateComponent, self)._fixture_setup()

        self.product = ProductFactory()

        # Any added component in tests will be added to this list and then remove them all
        self.components_to_delete = []

    def test_add_component(self):
        com = self.rpc_client.exec.Component.create({
            'name': 'application',
            'product': self.product.pk,
        })
        self.components_to_delete.append(com['id'])
        self.assertIsNotNone(com)
        self.assertEqual(com['name'], 'application')
        self.assertEqual(com['initial_owner'], self.api_user.username)

    def test_add_component_with_no_perms(self):
        self.rpc_client.exec.Auth.logout()
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.exec.Component.create(self.product.pk, "MyComponent")


class TestUpdateComponent(XmlrpcAPIBaseTest):
    # pylint: disable=objects-update-used
    def _fixture_setup(self):
        super(TestUpdateComponent, self)._fixture_setup()

        self.product = ProductFactory(name='StarCraft')
        self.component = ComponentFactory(name="application", product=self.product,
                                          initial_owner=None, initial_qa_contact=None)

    def test_update_component(self):
        values = {'name': 'Updated'}
        com = self.rpc_client.exec.Component.update(self.component.pk, values)
        self.assertEqual(com['name'], 'Updated')

    def test_update_component_with_non_exist(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Component matching query does not exist'):
            self.rpc_client.exec.Component.update(-99, {'name': 'new name'})

    def test_update_component_with_no_perms(self):
        self.rpc_client.exec.Auth.logout()
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.exec.Component.update(self.component.pk, {})
