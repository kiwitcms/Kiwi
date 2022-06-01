# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, invalid-name, objects-update-used

from xmlrpc.client import Fault as XmlRPCFault

from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase
from tcms.testcases.models import Category
from tcms.tests.factories import CategoryFactory, ProductFactory


class TestCategory(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.product_nitrate = ProductFactory(name="nitrate")
        self.product_xmlrpc = ProductFactory(name="xmlrpc")
        self.case_categories = [
            CategoryFactory(name="auto", product=self.product_nitrate),
            CategoryFactory(name="manual", product=self.product_nitrate),
            CategoryFactory(name="pending", product=self.product_xmlrpc),
        ]

    def test_filter_by_name_and_product_id(self):
        result = self.rpc_client.Category.filter(
            {"name": "manual", "product": self.product_nitrate.pk}
        )[0]

        self.assertEqual(result["name"], "manual")
        self.assertEqual(result["name"], "manual")
        self.assertEqual(result["product"], self.product_nitrate.pk)
        self.assertEqual(result["description"], "")

    def test_filter_by_product_id(self):
        categories = self.rpc_client.Category.filter(
            {"product": self.product_nitrate.pk}
        )
        self.assertIsNotNone(categories)

        category_names = []
        for category in categories:
            category_names.append(category["name"])

        self.assertEqual(3, len(category_names))
        self.assertIn("--default--", category_names)
        self.assertIn("auto", category_names)
        self.assertIn("manual", category_names)

    def test_filter_non_existing_doesnt_raise(self):
        found = self.rpc_client.Category.filter({"pk": -9})
        self.assertEqual(0, len(found))


class TestCategoryCreatePermissions(APIPermissionsTestCase):
    permission_label = "testcases.add_category"

    def _fixture_setup(self):
        super()._fixture_setup()
        self.product = ProductFactory()

    def verify_api_with_permission(self):
        result = self.rpc_client.Category.create(
            {"product": self.product.pk, "name": "Category with Permissions"}
        )

        # verify the serialized result
        self.assertIn("id", result)
        self.assertEqual(result["name"], "Category with Permissions")
        self.assertEqual(result["product"], self.product.pk)

        # verify the object from the DB
        category = Category.objects.get(pk=result["id"])
        self.assertEqual(category.name, "Category with Permissions")
        self.assertEqual(category.product_id, self.product.pk)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Category.create"'
        ):
            self.rpc_client.Category.create(
                {"product": self.product.pk, "name": "Category without Permissions"}
            )
