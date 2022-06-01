# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, attribute-defined-outside-init, objects-update-used

from xmlrpc.client import Fault as XmlRPCFault

from django.test import override_settings

from tcms.rpc.tests.utils import APITestCase
from tcms.tests.factories import BuildFactory, VersionFactory


@override_settings(LANGUAGE_CODE="en")
class BuildCreate(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.version = VersionFactory()

    def test_build_create_with_no_perms(self):
        self.rpc_client.Auth.logout()
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Build.create"'
        ):
            self.rpc_client.Build.create({})

    def test_build_create_with_no_required_fields(self):
        values = {"is_active": False}
        with self.assertRaisesRegex(
            XmlRPCFault, "name.*This field is required.*version.*This field is required"
        ):
            self.rpc_client.Build.create(values)

        values["name"] = "TB"
        with self.assertRaisesRegex(XmlRPCFault, "version.*This field is required"):
            self.rpc_client.Build.create(values)

        del values["name"]
        values["version"] = self.version.pk
        with self.assertRaisesRegex(XmlRPCFault, "name.*This field is required"):
            self.rpc_client.Build.create(values)

    def test_build_create_with_non_existing_version(self):
        values = {"version": -1, "name": "B7", "is_active": False}
        with self.assertRaisesRegex(XmlRPCFault, "version.*Select a valid choice"):
            self.rpc_client.Build.create(values)

        values["version"] = "AAAAAAAAAA"
        with self.assertRaisesRegex(XmlRPCFault, "version.*Select a valid choice"):
            self.rpc_client.Build.create(values)

    def test_build_create_with_chinese(self):
        # also see https://github.com/kiwitcms/Kiwi/issues/1770
        values = {"version": self.version.pk, "name": "开源中国", "is_active": False}
        b = self.rpc_client.Build.create(values)
        self.assertIsNotNone(b)
        self.assertEqual(b["version"], self.version.pk)
        self.assertEqual(b["name"], "开源中国")
        self.assertEqual(b["is_active"], False)

    def test_build_create(self):
        values = {"version": self.version.pk, "name": "B7"}
        b = self.rpc_client.Build.create(values)
        self.assertIsNotNone(b)
        self.assertEqual(b["version"], self.version.pk)
        self.assertEqual(b["name"], "B7")
        self.assertTrue(b["is_active"])


@override_settings(LANGUAGE_CODE="en")
class BuildUpdate(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.version = VersionFactory()
        self.another_version = VersionFactory()

        self.build_1 = BuildFactory(version=self.version)
        self.build_2 = BuildFactory(version=self.version)
        self.build_3 = BuildFactory(version=self.version)

    def test_build_update_with_non_existing_build(self):
        with self.assertRaisesRegex(XmlRPCFault, "Build matching query does not exist"):
            self.rpc_client.Build.update(-99, {})

    def test_build_update_with_no_perms(self):
        self.rpc_client.Auth.logout()
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Build.update"'
        ):
            self.rpc_client.Build.update(self.build_1.pk, {})

    def test_build_update_with_multi_id(self):
        builds = (self.build_1.pk, self.build_2.pk, self.build_3.pk)
        with self.assertRaisesRegex(XmlRPCFault, "Invalid parameter"):
            self.rpc_client.Build.update(builds, {})

    def test_build_update_with_non_existing_version_id(self):
        with self.assertRaisesRegex(XmlRPCFault, "version.*Select a valid choice"):
            self.rpc_client.Build.update(self.build_1.pk, {"version": -9999})

    def test_build_update(self):
        b = self.rpc_client.Build.update(
            self.build_3.pk,
            {
                "version": self.another_version.pk,
                "name": "Update",
            },
        )
        self.assertIsNotNone(b)
        self.assertEqual(b["version"], self.another_version.pk)
        self.assertEqual(b["name"], "Update")


class BuildFilter(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.version = VersionFactory()
        self.build = BuildFactory(version=self.version)

    def test_build_filter_with_non_exist_id(self):
        self.assertEqual(0, len(self.rpc_client.Build.filter({"pk": -9999})))

    def test_build_filter_with_id(self):
        b = self.rpc_client.Build.filter({"pk": self.build.pk})[0]
        self.assertIsNotNone(b)
        self.assertEqual(b["id"], self.build.pk)
        self.assertEqual(b["name"], self.build.name)
        self.assertEqual(b["version"], self.version.pk)
        self.assertTrue(b["is_active"])

    def test_build_filter_with_name_and_version(self):
        b = self.rpc_client.Build.filter(
            {"name": self.build.name, "version": self.version.pk}
        )[0]
        self.assertIsNotNone(b)
        self.assertEqual(b["id"], self.build.pk)
        self.assertEqual(b["name"], self.build.name)
        self.assertEqual(b["version"], self.version.pk)
        self.assertEqual(b["is_active"], True)
