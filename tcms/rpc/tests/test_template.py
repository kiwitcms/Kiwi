# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, invalid-name, objects-update-used
#
# Copyright (c) 2025 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html


from tcms.rpc.tests.utils import APIPermissionsTestCase
from tcms.testcases.models import Template
from tcms.xmlrpc_wrapper import XmlRPCFault


class TemplateCreate(APIPermissionsTestCase):
    permission_label = "testcases.add_template"

    def verify_api_with_permission(self):
        result = self.rpc_client.Template.create(
            {
                "name": "API test",
                "text": """
- Method name:
- Method URL:
- Input data:
- Expected result:""",
            }
        )

        # verify the serialized result
        self.assertIn("id", result)
        self.assertEqual(result["name"], "API test")
        self.assertIn("Method URL", result["text"])

        # verify the object from the DB
        template = Template.objects.get(pk=result["id"])
        self.assertEqual(template.name, result["name"])
        self.assertEqual(template.text, result["text"])

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Template.create"'
        ):
            self.rpc_client.Template.create(
                {
                    "name": "1-2-3",
                    "text": """
1) Do:
2) Do:
3) Result should be:""",
                }
            )


class TestTemplateFilter(APIPermissionsTestCase):
    permission_label = "testcases.view_template"

    def verify_api_with_permission(self):
        result = self.rpc_client.Template.filter(
            {
                "name": "Gherkin syntax",
            }
        )[0]

        self.assertIn("id", result)
        self.assertEqual(result["name"], "Gherkin syntax")
        self.assertIn("what behavior will be tested", result["text"])

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Template.filter"'
        ):
            self.rpc_client.Template.filter({})
