# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

from tcms.tests.factories import ProductFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestFilter(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestFilter, self)._fixture_setup()

        self.product = ProductFactory(name='Nitrate')
        self.product_xmlrpc = ProductFactory(name='XMLRPC API')

    def test_filter_by_id(self):
        prod = self.rpc_client.exec.Product.filter({"id": self.product.pk})
        self.assertIsNotNone(prod)
        self.assertEqual(prod[0]['name'], 'Nitrate')

    def test_filter_by_name(self):
        prod = self.rpc_client.exec.Product.filter({'name': 'Nitrate'})
        self.assertIsNotNone(prod)
        self.assertEqual(prod[0]['name'], 'Nitrate')

    def test_filter_non_existing(self):
        found = self.rpc_client.exec.Product.filter({'name': "Non Existing"})
        self.assertEqual(0, len(found))
