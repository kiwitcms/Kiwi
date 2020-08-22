# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, attribute-defined-outside-init, objects-update-used

from xmlrpc.client import Fault as XmlRPCFault
from xmlrpc.client import ProtocolError

from tcms.rpc.tests.utils import APITestCase
from tcms.tests.factories import BuildFactory, ProductFactory


class BuildCreate(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()

        self.product = ProductFactory()

    def test_build_create_with_no_args(self):
        bad_args = ([], (), {})
        for arg in bad_args:
            with self.assertRaisesRegex(XmlRPCFault, 'Internal error:'):
                self.rpc_client.Build.create(arg)

    def test_build_create_with_no_perms(self):
        self.rpc_client.Auth.logout()
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.Build.create({})

    def test_build_create_with_no_required_fields(self):
        values = {
            "is_active": False
        }
        with self.assertRaisesRegex(XmlRPCFault, 'Product and name are both required'):
            self.rpc_client.Build.create(values)

        values["name"] = "TB"
        with self.assertRaisesRegex(XmlRPCFault, 'Product and name are both required'):
            self.rpc_client.Build.create(values)

        del values["name"]
        values["product"] = self.product.pk
        with self.assertRaisesRegex(XmlRPCFault, 'Product and name are both required'):
            self.rpc_client.Build.create(values)

    def test_build_create_with_non_existing_product(self):
        values = {
            "product": 9999,
            "name": "B7",
            "is_active": False
        }
        with self.assertRaisesRegex(XmlRPCFault, 'Product matching query does not exist'):
            self.rpc_client.Build.create(values)

        values['product'] = "AAAAAAAAAA"
        with self.assertRaisesRegex(XmlRPCFault, 'Product matching query does not exist'):
            self.rpc_client.Build.create(values)

    def test_build_create_with_chinese(self):
        # also see https://github.com/kiwitcms/Kiwi/issues/1770
        values = {
            "product": self.product.pk,
            "name": "开源中国",
            "is_active": False
        }
        b = self.rpc_client.Build.create(values)
        self.assertIsNotNone(b)
        self.assertEqual(b['product_id'], self.product.pk)
        self.assertEqual(b['name'], "开源中国")
        self.assertEqual(b['is_active'], False)

    def test_build_create(self):
        values = {
            "product": self.product.pk,
            "name": "B7",
            "is_active": False
        }
        b = self.rpc_client.Build.create(values)
        self.assertIsNotNone(b)
        self.assertEqual(b['product_id'], self.product.pk)
        self.assertEqual(b['name'], "B7")
        self.assertEqual(b['is_active'], False)


class BuildUpdate(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()

        self.product = ProductFactory()
        self.another_product = ProductFactory()

        self.build_1 = BuildFactory(product=self.product)
        self.build_2 = BuildFactory(product=self.product)
        self.build_3 = BuildFactory(product=self.product)

    def test_build_update_with_non_existing_build(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Build matching query does not exist'):
            self.rpc_client.Build.update(-99, {})

    def test_build_update_with_no_perms(self):
        self.rpc_client.Auth.logout()
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.Build.update(self.build_1.pk, {})

    def test_build_update_with_multi_id(self):
        builds = (self.build_1.pk, self.build_2.pk, self.build_3.pk)
        with self.assertRaisesRegex(XmlRPCFault, 'Invalid parameter'):
            self.rpc_client.Build.update(builds, {})

    def test_build_update_with_non_existing_product_id(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Product matching query does not exist'):
            self.rpc_client.Build.update(self.build_1.pk, {"product": -9999})

    def test_build_update_with_non_existing_product_name(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Product matching query does not exist'):
            self.rpc_client.Build.update(self.build_1.pk, {"product": "AAAAAAAAAAAAAA"})

    def test_build_update(self):
        b = self.rpc_client.Build.update(self.build_3.pk, {
            "product": self.another_product.pk,
            "name": "Update",
        })
        self.assertIsNotNone(b)
        self.assertEqual(b['product_id'], self.another_product.pk)
        self.assertEqual(b['name'], 'Update')


class BuildFilter(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()

        self.product = ProductFactory()
        self.build = BuildFactory(product=self.product)

    def test_build_filter_with_non_exist_id(self):
        self.assertEqual(0, len(self.rpc_client.Build.filter({'pk': -9999})))

    def test_build_filter_with_id(self):
        b = self.rpc_client.Build.filter({'pk': self.build.pk})[0]
        self.assertIsNotNone(b)
        self.assertEqual(b['id'], self.build.pk)
        self.assertEqual(b['name'], self.build.name)
        self.assertEqual(b['product_id'], self.product.pk)
        self.assertTrue(b['is_active'])

    def test_build_filter_with_name_and_product(self):
        b = self.rpc_client.Build.filter({
            'name': self.build.name,
            'product': self.product.pk
        })[0]
        self.assertIsNotNone(b)
        self.assertEqual(b['id'], self.build.pk)
        self.assertEqual(b['name'], self.build.name)
        self.assertEqual(b['product_id'], self.product.pk)
        self.assertEqual(b['is_active'], True)
