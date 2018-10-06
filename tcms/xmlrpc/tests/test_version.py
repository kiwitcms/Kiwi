# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, invalid-name, avoid-list-comprehension

from xmlrpc.client import ProtocolError
from xmlrpc.client import Fault as XmlRPCFault

from tcms.tests.factories import ProductFactory
from tcms.tests.factories import VersionFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestFilterVersions(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestFilterVersions, self)._fixture_setup()

        self.product = ProductFactory(name='StarCraft')
        self.version = VersionFactory(value='0.7', product=self.product)

    def test_filter_by_version_id(self):
        ver = self.rpc_client.exec.Version.filter({'id': self.version.pk})
        self.assertIsNotNone(ver)
        self.assertEqual(ver[0]['value'], "0.7")

    def test_filter_by_product_id(self):
        versions = self.rpc_client.exec.Version.filter({'product_id': self.product.pk})
        self.assertIsInstance(versions, list)
        versions = [version['value'] for version in versions]
        self.assertEqual(2, len(versions))
        self.assertIn('0.7', versions)
        self.assertIn('unspecified', versions)

    def test_filter_by_name(self):
        ver = self.rpc_client.exec.Version.filter({'value': '0.7'})
        self.assertIsNotNone(ver)
        self.assertEqual(ver[0]['value'], "0.7")


class TestAddVersion(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestAddVersion, self)._fixture_setup()

        self.product_name = 'StarCraft'
        self.product = ProductFactory(name=self.product_name)

    def test_add_version_with_product_id(self):
        prod = self.rpc_client.exec.Version.create({
            "product": self.product.pk,
            "value": "New Version 1"
        })
        self.assertEqual(prod['value'], "New Version 1")
        self.assertEqual(prod['product_id'], self.product.pk)

    def test_add_version_with_product_name(self):
        new_version = 'New Version 2'
        prod = self.rpc_client.exec.Version.create({
            'product': self.product_name,
            'value': new_version,
        })
        self.assertEqual(prod['value'], new_version)
        self.assertEqual(prod['product_id'], self.product.pk)

    def test_add_version_with_non_exist_prod(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Product matching query does not exist'):
            self.rpc_client.exec.Version.create({
                "product": -9,
                "value": "0.1"
            })

    def test_add_version_with_missing_argument(self):
        with self.assertRaisesRegex(XmlRPCFault, "Internal error:.*value.*This field is required"):
            self.rpc_client.exec.Version.create({"product": self.product.pk})

        with self.assertRaisesRegex(XmlRPCFault, 'No product given'):
            self.rpc_client.exec.Version.create({"value": "0.1"})

    def test_add_version_with_extra_unrecognized_field(self):
        new_version = self.rpc_client.exec.Version.create({
            'product': self.product.pk,
            'value': 'New version',
            'extra-data-field': 'Extra value that is not expected',
        })
        self.assertEqual(self.product.pk, new_version['product_id'])
        self.assertEqual(self.product.name, new_version['product'])
        self.assertEqual('New version', new_version['value'])

    def test_add_version_with_no_perms(self):
        self.rpc_client.exec.Auth.logout()
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.exec.Version.create({})
