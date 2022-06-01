# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

from xmlrpc.client import Fault as XmlRPCFault

from tcms.management.models import Classification
from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase
from tcms.tests.factories import ClassificationFactory


class TestClassificationFilter(APITestCase):
    """Test Classification.filter method"""

    def _fixture_setup(self):
        super()._fixture_setup()

        self.classification = ClassificationFactory()

    def test_filter_classification(self):
        classifications = self.rpc_client.Classification.filter(
            {"id": self.classification.id}
        )

        self.assertGreater(len(classifications), 0)
        for classification in classifications:
            self.assertIsNotNone(classification["id"])
            self.assertIsNotNone(classification["name"])


class TestClassificationFilterPermissions(APIPermissionsTestCase):
    """Test permission for Classification.filter method"""

    permission_label = "management.view_classification"

    def _fixture_setup(self):
        super()._fixture_setup()

        self.classification = ClassificationFactory()

    def verify_api_with_permission(self):
        classifications = self.rpc_client.Classification.filter(
            {"id": self.classification.id}
        )
        self.assertGreater(len(classifications), 0)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Classification.filter"'
        ):
            self.rpc_client.Classification.filter({})


class TestClassificationCreate(APIPermissionsTestCase):
    permission_label = "management.add_classification"

    def verify_api_with_permission(self):
        result = self.rpc_client.Classification.create({"name": "API-CLASSIFICATION"})
        self.assertEqual(result["name"], "API-CLASSIFICATION")
        self.assertIn("name", result)
        self.assertIn("id", result)

        obj_from_db = Classification.objects.get(pk=result["id"])
        self.assertEqual(result["name"], obj_from_db.name)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Classification.create"'
        ):
            self.rpc_client.Classification.create({"name": "API-CLASSIFICATION"})
