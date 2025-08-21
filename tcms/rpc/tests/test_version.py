# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, invalid-name, avoid-list-comprehension


from django.test import override_settings

from tcms.management.models import Version
from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase
from tcms.tests.factories import ProductFactory, VersionFactory
from tcms.xmlrpc_wrapper import XmlRPCFault


class TestFilterVersions(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.product = ProductFactory(name="StarCraft")
        cls.version = VersionFactory(value="0.7", product=cls.product)

    def test_filter_by_version_id(self):
        result = self.rpc_client.Version.filter({"id": self.version.pk})[0]

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], self.version.pk)
        self.assertEqual(result["value"], "0.7")
        self.assertEqual(result["product"], self.version.product_id)

    def test_filter_by_product_id(self):
        versions = self.rpc_client.Version.filter({"product_id": self.product.pk})
        self.assertIsInstance(versions, list)
        versions = [version["value"] for version in versions]
        self.assertEqual(2, len(versions))
        self.assertIn("0.7", versions)
        self.assertIn("unspecified", versions)

    def test_filter_by_name(self):
        ver = self.rpc_client.Version.filter({"value": "0.7"})
        self.assertIsNotNone(ver)
        self.assertEqual(ver[0]["value"], "0.7")


@override_settings(LANGUAGE_CODE="en")
class TestVersionCreateFunctionality(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.product_name = "StarCraft"
        cls.product = ProductFactory(name=cls.product_name)

    def test_add_version_with_product_id(self):
        result = self.rpc_client.Version.create(
            {"product": self.product.pk, "value": "New Version 1"}
        )
        self.assertEqual(result["value"], "New Version 1")
        self.assertEqual(result["product"], self.product.pk)
        self.assertIn("id", result)

    def test_add_version_with_non_exist_prod(self):
        with self.assertRaisesRegex(XmlRPCFault, ".*product.*Select a valid choice.*"):
            self.rpc_client.Version.create({"product": -9, "value": "0.1"})

    def test_add_version_with_missing_argument(self):
        with self.assertRaisesRegex(
            XmlRPCFault, "Internal error:.*value.*This field is required"
        ):
            self.rpc_client.Version.create({"product": self.product.pk})

        with self.assertRaisesRegex(
            XmlRPCFault, "Internal error:.*product.*This field is required"
        ):
            self.rpc_client.Version.create({"value": "0.1"})

    def test_add_version_with_extra_unrecognized_field(self):
        new_version = self.rpc_client.Version.create(
            {
                "product": self.product.pk,
                "value": "New version",
                "extra-data-field": "Extra value that is not expected",
            }
        )
        self.assertEqual(self.product.pk, new_version["product"])
        self.assertEqual("New version", new_version["value"])


class TestVersionCreatePermissions(APIPermissionsTestCase):
    permission_label = "management.add_version"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()
        cls.product = ProductFactory()

    def verify_api_with_permission(self):
        result = self.rpc_client.Version.create(
            {"product": self.product.pk, "value": "Version with Permissions"}
        )

        # verify the serialized result
        self.assertIn("id", result)
        self.assertEqual(result["value"], "Version with Permissions")
        self.assertEqual(result["product"], self.product.pk)

        # verify the object from the DB
        version = Version.objects.get(pk=result["id"])
        self.assertEqual(version.value, "Version with Permissions")
        self.assertEqual(version.product_id, self.product.pk)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Version.create"'
        ):
            self.rpc_client.Version.create(
                {"product": self.product.pk, "value": "Version without Permissions"}
            )
