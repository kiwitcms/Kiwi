# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init


from tcms.management.models import Product
from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase
from tcms.tests.factories import ClassificationFactory, ProductFactory
from tcms.xmlrpc_wrapper import XmlRPCFault


class TestFilter(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.product = ProductFactory(name="Kiwi TCMS")
        cls.product_xmlrpc = ProductFactory(name="XMLRPC API")

    def test_filter_by_id(self):
        result = self.rpc_client.Product.filter({"id": self.product.pk})
        self.assertIsNotNone(result)
        self.assertEqual(result[0]["name"], "Kiwi TCMS")
        self.assertEqual(result[0]["description"], "")
        self.assertIn("classification", result[0])

    def test_filter_non_existing(self):
        result = self.rpc_client.Product.filter({"name": "Non Existing"})
        self.assertEqual(0, len(result))


class TestProductCreatePermissions(APIPermissionsTestCase):
    permission_label = "management.add_product"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()
        cls.classification = ClassificationFactory()

    def verify_api_with_permission(self):
        result = self.rpc_client.Product.create(
            {
                "name": "Product with Permissions",
                "classification": self.classification.pk,
            }
        )

        # verify the serialized result
        self.assertEqual(result["name"], "Product with Permissions")
        self.assertEqual(result["description"], "")
        self.assertIn("classification", result)

        # verify the object from the DB
        product = Product.objects.get(pk=result["id"])
        self.assertEqual(product.name, "Product with Permissions")

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Product.create"'
        ):
            self.rpc_client.Product.create(
                {
                    "name": "Product with Permissions",
                    "classification": self.classification.pk,
                }
            )
