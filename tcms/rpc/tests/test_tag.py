# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

from django.conf import settings

from tcms.rpc.tests.utils import APITestCase
from tcms.tests.factories import TagFactory


class Tag(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.tag_db = TagFactory(name="db")
        cls.tag_fedora = TagFactory(name="fedora")
        cls.tag_python = TagFactory(name="python")
        cls.tag_tests = TagFactory(name="tests")
        cls.tag_xmlrpc = TagFactory(name="xmlrpc")
        cls.tags = [
            cls.tag_db,
            cls.tag_fedora,
            cls.tag_python,
            cls.tag_tests,
            cls.tag_xmlrpc,
        ]

    def test_get_tags_with_ids(self):
        test_tag = self.rpc_client.Tag.filter(
            {"id__in": [self.tag_python.pk, self.tag_db.pk, self.tag_fedora.pk]}
        )
        self.assertIsNotNone(test_tag)
        self.assertEqual(3, len(test_tag))

        test_tag = sorted(test_tag, key=lambda item: item["id"])
        self.assertEqual(test_tag[0]["id"], self.tag_db.pk)
        self.assertEqual(test_tag[0]["name"], "db")
        self.assertEqual(test_tag[1]["id"], self.tag_fedora.pk)
        self.assertEqual(test_tag[1]["name"], "fedora")
        self.assertEqual(test_tag[2]["id"], self.tag_python.pk)
        self.assertEqual(test_tag[2]["name"], "python")

    def test_get_tags_with_names(self):
        test_tag = self.rpc_client.Tag.filter({"name__in": ["python", "fedora", "db"]})
        self.assertIsNotNone(test_tag)
        self.assertEqual(3, len(test_tag))

        test_tag = sorted(test_tag, key=lambda item: item["id"])
        self.assertEqual(test_tag[0]["id"], self.tag_db.pk)
        self.assertEqual(test_tag[0]["name"], "db")
        self.assertEqual(test_tag[1]["id"], self.tag_fedora.pk)
        self.assertEqual(test_tag[1]["name"], "fedora")
        self.assertEqual(test_tag[2]["id"], self.tag_python.pk)
        self.assertEqual(test_tag[2]["name"], "python")

        if "tcms.bugs.apps.AppConfig" in settings.INSTALLED_APPS:
            self.assertIn("bugs", test_tag[0])

        self.assertIn("case", test_tag[0])
        self.assertIn("plan", test_tag[0])
        self.assertIn("run", test_tag[0])
