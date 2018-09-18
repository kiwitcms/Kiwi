# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

from tcms.testruns.models import TestRun

from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TagFactory
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
        self.rpc_client.exec.TestRun.add_tag(self.test_runs[0].pk, self.tag0.name)
        tag_exists = TestRun.objects.filter(pk=self.test_runs[0].pk, tag__pk=self.tag0.pk).exists()
        self.assertTrue(tag_exists)


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

        self.test_runs[0].add_tag(self.tag0)
        self.test_runs[1].add_tag(self.tag1)

    def test_remove_tag(self):
        self.rpc_client.exec.TestRun.remove_tag(self.test_runs[0].pk, self.tag0.name)
        tag_exists = TestRun.objects.filter(pk=self.test_runs[0].pk, tag__pk=self.tag0.pk).exists()
        self.assertFalse(tag_exists)


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
