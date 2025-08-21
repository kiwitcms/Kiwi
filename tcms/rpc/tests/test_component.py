# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, invalid-name


from tcms.rpc.tests.utils import APITestCase
from tcms.tests.factories import ComponentFactory, ProductFactory
from tcms.xmlrpc_wrapper import XmlRPCFault


class TestFilterComponents(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.product = ProductFactory(name="StarCraft")
        cls.component = ComponentFactory(
            name="application",
            product=cls.product,
            initial_owner=None,
            initial_qa_contact=None,
        )

    def test_filter_by_product_id(self):
        result = self.rpc_client.Component.filter({"product": self.product.pk})[0]
        self.assertIsNotNone(result)

        self.assertEqual(result["id"], self.component.pk)
        self.assertEqual(result["name"], "application")
        self.assertEqual(result["product"], self.product.pk)
        self.assertIn("description", result)
        self.assertIn("initial_owner", result)
        self.assertIn("initial_qa_contact", result)

    def test_filter_by_name(self):
        com = self.rpc_client.Component.filter({"name": "application"})
        self.assertIsNotNone(com)
        self.assertEqual(com[0]["name"], "application")

    def test_filter_non_existing(self):
        found = self.rpc_client.Component.filter({"name": "documentation"})
        self.assertEqual(0, len(found))


class TestCreateComponent(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.product = ProductFactory()

    def test_add_component(self):
        result = self.rpc_client.Component.create(
            {
                "name": "application",
                "product": self.product.pk,
            }
        )
        self.assertIsNotNone(result)

        self.assertIn("id", result)
        self.assertEqual(result["name"], "application")
        self.assertEqual(result["product"], self.product.pk)
        self.assertEqual(result["initial_owner"], self.api_user.pk)
        self.assertEqual(result["initial_qa_contact"], self.api_user.pk)
        self.assertEqual(result["description"], "Created via API")

    def test_add_component_with_no_perms(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Component.create"'
        ):
            # assign to a temp variable b/c self.rpc_client a property and calling it twice
            # in sequence results in 1st call logging out and 2nd call logging in automatically
            rpc_client = self.rpc_client

            rpc_client.Auth.logout()
            rpc_client.Component.create(self.product.pk, "MyComponent")


# pylint: disable=objects-update-used
class TestUpdateComponent(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.product = ProductFactory(name="StarCraft")
        cls.component = ComponentFactory(
            name="application",
            product=cls.product,
            initial_owner=None,
            initial_qa_contact=None,
        )

    def test_update_component(self):
        values = {"name": "Updated"}
        com = self.rpc_client.Component.update(self.component.pk, values)
        self.assertEqual(com["name"], "Updated")

    def test_update_component_with_non_exist(self):
        with self.assertRaisesRegex(
            XmlRPCFault, "Component matching query does not exist"
        ):
            self.rpc_client.Component.update(-99, {"name": "new name"})

    def test_update_component_with_no_perms(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Component.update"'
        ):
            # assign to a temp variable b/c self.rpc_client a property and calling it twice
            # in sequence results in 1st call logging out and 2nd call logging in automatically
            rpc_client = self.rpc_client

            rpc_client.Auth.logout()
            rpc_client.Component.update(self.component.pk, {})
