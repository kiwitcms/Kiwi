# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

from xmlrpc.client import ProtocolError

from tcms_api.xmlrpc import TCMSXmlrpc

from tcms.testruns.models import TestRun

from tcms.tests import remove_perm_from_user
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TagFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


__all__ = (
    'TestAddTag',
    'TestRemoveTag',
)


class TestAddTag(XmlrpcAPIBaseTest):
    def _fixture_setup(self):
        super(TestAddTag, self)._fixture_setup()

        self.product = ProductFactory()
        self.version = VersionFactory()
        self.build = self.product.build.all()[0]
        self.plan = TestPlanFactory(author=self.api_user, owner=self.api_user, product=self.product)

        self.test_runs = [
            TestRunFactory(product_version=self.version, build=self.build,
                           default_tester=None, plan=self.plan),
            TestRunFactory(product_version=self.version, build=self.build,
                           default_tester=None, plan=self.plan),
        ]

        self.tag0 = TagFactory(name='xmlrpc_test_tag_0')
        self.tag1 = TagFactory(name='xmlrpc_test_tag_1')

    def test_add_tag(self):
        result = self.rpc_client.exec.TestRun.add_tag(self.test_runs[0].pk, self.tag0.name)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], self.tag0.pk)
        self.assertEqual(result[0]['name'], self.tag0.name)

        tag_exists = TestRun.objects.filter(pk=self.test_runs[0].pk, tag__pk=self.tag0.pk).exists()
        self.assertTrue(tag_exists)

    def test_add_tag_without_permissions(self):
        unauthorized_user = UserFactory()
        unauthorized_user.set_password('api-testing')
        unauthorized_user.save()

        remove_perm_from_user(unauthorized_user, 'testruns.add_testruntag')

        rpc_client = TCMSXmlrpc(unauthorized_user.username,
                                'api-testing',
                                '%s/xml-rpc/' % self.live_server_url).server

        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            rpc_client.TestRun.add_tag(self.test_runs[0].pk, self.tag0.name)

        # tags were not modified
        tag_exists = TestRun.objects.filter(pk=self.test_runs[0].pk, tag__pk=self.tag0.pk).exists()
        self.assertFalse(tag_exists)


class TestRemoveTag(XmlrpcAPIBaseTest):
    def _fixture_setup(self):
        super(TestRemoveTag, self)._fixture_setup()

        self.product = ProductFactory()
        self.version = VersionFactory()
        self.build = self.product.build.all()[0]
        self.plan = TestPlanFactory(author=self.api_user, owner=self.api_user, product=self.product)

        self.test_runs = [
            TestRunFactory(product_version=self.version, build=self.build,
                           default_tester=None, plan=self.plan),
            TestRunFactory(product_version=self.version, build=self.build,
                           default_tester=None, plan=self.plan),
        ]

        self.tag0 = TagFactory(name='xmlrpc_test_tag_0')
        self.tag1 = TagFactory(name='xmlrpc_test_tag_1')

        for tag in [self.tag0, self.tag1]:
            self.test_runs[0].add_tag(tag)
            self.test_runs[1].add_tag(tag)

    def test_remove_tag(self):
        result = self.rpc_client.exec.TestRun.remove_tag(self.test_runs[0].pk, self.tag0.name)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], self.tag1.pk)
        self.assertEqual(result[0]['name'], self.tag1.name)

        tag_exists = TestRun.objects.filter(pk=self.test_runs[0].pk, tag__pk=self.tag0.pk).exists()
        self.assertFalse(tag_exists)

        tag_exists = TestRun.objects.filter(pk=self.test_runs[0].pk, tag__pk=self.tag1.pk).exists()
        self.assertTrue(tag_exists)

    def test_remove_tag_without_permissions(self):
        unauthorized_user = UserFactory()
        unauthorized_user.set_password('api-testing')
        unauthorized_user.save()

        remove_perm_from_user(unauthorized_user, 'testruns.delete_testruntag')

        rpc_client = TCMSXmlrpc(unauthorized_user.username,
                                'api-testing',
                                '%s/xml-rpc/' % self.live_server_url).server

        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            rpc_client.TestRun.remove_tag(self.test_runs[0].pk, self.tag0.name)

        # tags were not modified
        tag_exists = TestRun.objects.filter(pk=self.test_runs[0].pk, tag__pk=self.tag0.pk).exists()
        self.assertTrue(tag_exists)

        tag_exists = TestRun.objects.filter(pk=self.test_runs[0].pk, tag__pk=self.tag1.pk).exists()
        self.assertTrue(tag_exists)


class TestProductVersionWhenCreating(XmlrpcAPIBaseTest):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.product = ProductFactory()
        self.version = VersionFactory()
        self.build = self.product.build.first()
        self.plan = TestPlanFactory(author=self.api_user,
                                    owner=self.api_user,
                                    product=self.product,
                                    product_version=self.version)

    def test_create_without_product_version(self):
        test_run_fields = {
            'plan': self.plan.pk,
            'build': self.build.pk,
            'summary': 'TR without product_version',
            'manager': self.api_user.username,
        }

        result = self.rpc_client.exec.TestRun.create(test_run_fields)
        self.assertEqual(result['product_version'], self.plan.product_version.value)

    def test_create_with_product_version(self):
        version2 = VersionFactory()

        test_run_fields = {
            'plan': self.plan.pk,
            'build': self.build.pk,
            'summary': 'TR with product_version',
            'manager': self.api_user.pk,
            'product_version': version2.pk,
        }

        result = self.rpc_client.exec.TestRun.create(test_run_fields)
        # the result is still using product_version from TR.plan.product_version
        # not the one we specified above
        self.assertEqual(result['product_version'], self.plan.product_version.value)
