# -*- coding: utf-8 -*-

from xmlrpc.client import Fault as XmlRPCFault

from tcms.testruns.models import TestRun

from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestTagFactory
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

        self.tag0 = TestTagFactory(name='xmlrpc_test_tag_0')
        self.tag1 = TestTagFactory(name='xmlrpc_test_tag_1')
        self.tag_name = 'xmlrpc_tag_name_1'

    def test_single_id(self):
        '''Test with singal plan id and tag id'''
        with self.assertRaisesRegex(XmlRPCFault,
                                    ".*Parameter tags must be a string or list\(string\).*"):
            self.rpc_client.TestRun.add_tag(self.test_runs[0].pk, self.tag0.pk)

        self.rpc_client.TestRun.add_tag(self.test_runs[0].pk, self.tag0.name)
        tag_exists = TestRun.objects.filter(pk=self.test_runs[0].pk, tag__pk=self.tag0.pk).exists()
        self.assertTrue(tag_exists)

    def test_array_argument(self):
        self.rpc_client.TestRun.add_tag(self.test_runs[0].pk, [self.tag1.name, self.tag_name])
        tag_exists = TestRun.objects.filter(pk=self.test_runs[0].pk,
                                            tag__name__in=[self.tag1.name, self.tag_name])
        self.assertTrue(tag_exists.exists())

        runs_ids = [run.pk for run in self.test_runs]
        tags_names = [self.tag_name, 'xmlrpc_tag_name_2']
        self.rpc_client.TestRun.add_tag(runs_ids, tags_names)
        for run in self.test_runs:
            tag_exists = run.tag.filter(name__in=tags_names).exists()
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

        self.tag0 = TestTagFactory(name='xmlrpc_test_tag_0')
        self.tag1 = TestTagFactory(name='xmlrpc_test_tag_1')

        self.test_runs[0].add_tag(self.tag0)
        self.test_runs[1].add_tag(self.tag1)

        self.tag_name = 'xmlrpc_tag_name_1'

    def test_single_id(self):
        '''Test with single plan id and tag id'''
        # removing by ID raises an error
        with self.assertRaisesRegex(XmlRPCFault,
                                    ".*Parameter tags must be a string or list\(string\).*"):
            self.rpc_client.TestRun.remove_tag(self.test_runs[0].pk, self.tag0.pk)

        # removing by name works fine
        self.rpc_client.TestRun.remove_tag(self.test_runs[0].pk, self.tag0.name)
        tag_exists = TestRun.objects.filter(pk=self.test_runs[0].pk, tag__pk=self.tag0.pk).exists()
        self.assertFalse(tag_exists)

    def test_array_argument(self):
        self.rpc_client.TestRun.remove_tag(self.test_runs[0].pk, [self.tag0.name, self.tag_name])
        tag_exists = TestRun.objects.filter(pk=self.test_runs[0].pk,
                                            tag__name__in=[self.tag0.name, self.tag_name])
        self.assertFalse(tag_exists.exists())

        runs_ids = [run.pk for run in self.test_runs]
        tags_names = [self.tag_name, 'xmlrpc_tag_name_2']
        self.rpc_client.TestRun.remove_tag(runs_ids, tags_names)
        for run in self.test_runs:
            tag_exists = run.tag.filter(name__in=tags_names).exists()
            self.assertFalse(tag_exists)
