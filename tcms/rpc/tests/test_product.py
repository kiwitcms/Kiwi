# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

from tcms.rpc.tests.utils import APITestCase
from tcms.tests.factories import ProductFactory


class TestFilter(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.product = ProductFactory(name="Kiwi TCMS")
        self.product_xmlrpc = ProductFactory(name="XMLRPC API")

    def test_filter_by_id(self):
        prod = self.rpc_client.Product.filter({"id": self.product.pk})
        self.assertIsNotNone(prod)
        self.assertEqual(prod[0]["name"], "Kiwi TCMS")

    def test_filter_by_name(self):
        prod = self.rpc_client.Product.filter({"name": "Kiwi TCMS"})
        self.assertIsNotNone(prod)
        self.assertEqual(prod[0]["name"], "Kiwi TCMS")

    def test_filter_non_existing(self):
        found = self.rpc_client.Product.filter({"name": "Non Existing"})
        self.assertEqual(0, len(found))
