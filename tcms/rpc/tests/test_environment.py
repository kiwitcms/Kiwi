# -*- coding: utf-8 -*-

from django.test import override_settings

from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase
from tcms.testruns.models import Environment, EnvironmentProperty
from tcms.xmlrpc_wrapper import XmlRPCFault


class TestFilterPermission(APIPermissionsTestCase):
    permission_label = "testruns.view_environment"

    def verify_api_with_permission(self):
        result = self.rpc_client.Environment.filter()
        self.assertTrue(isinstance(result, list))

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Environment.filter"'
        ):
            self.rpc_client.Environment.filter(None)


@override_settings(LANGUAGE_CODE="en")
class EnvironmentCreate(APITestCase):
    def test_environment_create_with_no_required_fields(self):
        values = {}
        with self.assertRaisesRegex(XmlRPCFault, "name.*This field is required."):
            self.rpc_client.Environment.create(values)

        values["description"] = "Description"
        with self.assertRaisesRegex(XmlRPCFault, "name.*This field is required"):
            self.rpc_client.Environment.create(values)

    def test_environment_duplicate(self):
        values = {"name": "E7", "description": "Description"}
        self.rpc_client.Environment.create(values)
        with self.assertRaisesRegex(
            XmlRPCFault, "name.*Environment with this Name already exists"
        ):
            self.rpc_client.Environment.create(values)


class TestEnvironmentCreatePermissions(APIPermissionsTestCase):
    permission_label = "testruns.add_environment"

    def verify_api_with_permission(self):
        name = "E7"
        description = "Environment with Permissions"
        values = {"name": name, "description": description}
        result = self.rpc_client.Environment.create(values)

        # verify the serialized result
        self.assertIn("id", result)
        self.assertEqual(result["name"], name)
        self.assertEqual(result["description"], description)

        # verify the object from the DB
        environment = Environment.objects.get(pk=result["id"])
        self.assertEqual(environment.name, name)
        self.assertEqual(environment.description, description)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Environment.create"'
        ):
            self.rpc_client.Environment.create(
                {"name": "E8", "description": "Environment without Permissions"}
            )


class EnvironmentRemoveProperty(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.environment = Environment.objects.create(name="E9")
        cls.property = EnvironmentProperty.objects.create(
            environment=cls.environment, name="os", value="Linux"
        )
        cls.another_property = EnvironmentProperty.objects.create(
            environment=cls.environment, name="arch", value="x86_64"
        )

    def test_remove_property(self):
        self.rpc_client.Environment.remove_property({"pk": self.property.pk})

        properties = EnvironmentProperty.objects.filter(environment=self.environment)
        self.assertNotIn(self.property, properties)
        self.assertIn(self.another_property, properties)

    def test_remove_property_with_empty_query_raises_and_deletes_nothing(self):
        with self.assertRaisesRegex(
            XmlRPCFault, "Refusing an empty query: it would delete every record"
        ):
            self.rpc_client.Environment.remove_property({})

        self.assertEqual(
            EnvironmentProperty.objects.filter(environment=self.environment).count(), 2
        )
