# -*- coding: utf-8 -*-

from httplib import INTERNAL_SERVER_ERROR

from tcms.testruns.models import TestRun
from tcms.xmlrpc.api import testrun as XmlrpcTestRun
from tcms.xmlrpc.tests.utils import make_http_request

from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestTagFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest

__all__ = (
    'TestAddTag',
    'TestRemoveTag',
)


class TestAddTag(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.http_req = make_http_request(user=cls.user,
                                         user_perm='testruns.add_testruntag')

        cls.product = ProductFactory()
        cls.version = VersionFactory()
        cls.build = cls.product.build.all()[0]
        cls.plan = TestPlanFactory(author=cls.user, owner=cls.user, product=cls.product)

        cls.test_runs = [
            TestRunFactory(product_version=cls.version, build=cls.build,
                           default_tester=None, plan=cls.plan),
            TestRunFactory(product_version=cls.version, build=cls.build,
                           default_tester=None, plan=cls.plan),
        ]

        cls.tag0 = TestTagFactory(name='xmlrpc_test_tag_0')
        cls.tag1 = TestTagFactory(name='xmlrpc_test_tag_1')
        cls.tag_name = 'xmlrpc_tag_name_1'

    def test_single_id(self):
        '''Test with singal plan id and tag id'''
        self.assertRaisesXmlrpcFault(INTERNAL_SERVER_ERROR, XmlrpcTestRun.add_tag,
                                     self.http_req, self.test_runs[0].pk, self.tag0.pk)

        XmlrpcTestRun.add_tag(self.http_req, self.test_runs[0].pk, self.tag0.name)
        tag_exists = TestRun.objects.filter(pk=self.test_runs[0].pk, tag__pk=self.tag0.pk).exists()
        self.assertTrue(tag_exists)

    def test_array_argument(self):
        XmlrpcTestRun.add_tag(self.http_req, self.test_runs[0].pk, [self.tag1.name, self.tag_name])
        tag_exists = TestRun.objects.filter(pk=self.test_runs[0].pk,
                                            tag__name__in=[self.tag1.name, self.tag_name])
        self.assertTrue(tag_exists.exists())

        runs_ids = [run.pk for run in self.test_runs]
        tags_names = [self.tag_name, 'xmlrpc_tag_name_2']
        XmlrpcTestRun.add_tag(self.http_req, runs_ids, tags_names)
        for run in self.test_runs:
            tag_exists = run.tag.filter(name__in=tags_names).exists()
            self.assertTrue(tag_exists)


class TestRemoveTag(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.http_req = make_http_request(user=cls.user,
                                         user_perm='testruns.delete_testruntag')

        cls.product = ProductFactory()
        cls.version = VersionFactory()
        cls.build = cls.product.build.all()[0]
        cls.plan = TestPlanFactory(author=cls.user, owner=cls.user, product=cls.product)

        cls.test_runs = [
            TestRunFactory(product_version=cls.version, build=cls.build,
                           default_tester=None, plan=cls.plan),
            TestRunFactory(product_version=cls.version, build=cls.build,
                           default_tester=None, plan=cls.plan),
        ]

        cls.tag0 = TestTagFactory(name='xmlrpc_test_tag_0')
        cls.tag1 = TestTagFactory(name='xmlrpc_test_tag_1')

        cls.test_runs[0].add_tag(cls.tag0)
        cls.test_runs[1].add_tag(cls.tag1)

        cls.tag_name = 'xmlrpc_tag_name_1'

    def test_single_id(self):
        '''Test with single plan id and tag id'''
        # removing by ID raises an error
        self.assertRaisesXmlrpcFault(INTERNAL_SERVER_ERROR, XmlrpcTestRun.remove_tag,
                                     self.http_req, self.test_runs[0].pk, self.tag0.pk)

        # removing by name works fine
        XmlrpcTestRun.remove_tag(self.http_req, self.test_runs[0].pk, self.tag0.name)
        tag_exists = TestRun.objects.filter(pk=self.test_runs[0].pk, tag__pk=self.tag0.pk).exists()
        self.assertFalse(tag_exists)

    def test_array_argument(self):
        XmlrpcTestRun.remove_tag(self.http_req, self.test_runs[0].pk, [self.tag0.name, self.tag_name])
        tag_exists = TestRun.objects.filter(pk=self.test_runs[0].pk,
                                            tag__name__in=[self.tag0.name, self.tag_name])
        self.assertFalse(tag_exists.exists())

        runs_ids = [run.pk for run in self.test_runs]
        tags_names = [self.tag_name, 'xmlrpc_tag_name_2']
        XmlrpcTestRun.remove_tag(self.http_req, runs_ids, tags_names)
        for run in self.test_runs:
            tag_exists = run.tag.filter(name__in=tags_names).exists()
            self.assertFalse(tag_exists)
