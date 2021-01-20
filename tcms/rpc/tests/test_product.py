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
        result = self.rpc_client.Product.filter({"id": self.product.pk})
        self.assertIsNotNone(result)
        self.assertEqual(result[0]["name"], "Kiwi TCMS")
        self.assertEqual(result[0]["description"], "")
        self.assertIn("classification", result[0])

    def test_filter_non_existing(self):
        result = self.rpc_client.Product.filter({"name": "Non Existing"})
        self.assertEqual(0, len(result))
