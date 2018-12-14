# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, objects-update-used
from datetime import datetime
from xmlrpc.client import ProtocolError

from django.contrib.auth.models import Permission

from tcms_api.xmlrpc import TCMSXmlrpc

from tcms.testruns.models import TestRun, TestCaseRun

from tcms.tests import remove_perm_from_user
from tcms.tests.factories import TestCaseFactory, BuildFactory
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TagFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestAddCase(XmlrpcAPIBaseTest):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.plan = TestPlanFactory(author=self.api_user)

        self.test_case = TestCaseFactory()
        self.plan.add_case(self.test_case)

        self.test_run = TestRunFactory(plan=self.plan)

    def test_add_case(self):
        result = self.rpc_client.exec.TestRun.add_case(self.test_run.pk, self.test_case.pk)
        self.assertTrue(isinstance(result, dict))

        test_case_run = TestCaseRun.objects.get(run=self.test_run.pk, case=self.test_case.pk)
        self.assertEqual(test_case_run.pk, result['case_run_id'])
        self.assertEqual(test_case_run.case.pk, result['case_id'])
        self.assertEqual(test_case_run.run.pk, result['run_id'])

    def test_add_case_without_permissions(self):
        unauthorized_user = UserFactory()
        unauthorized_user.set_password('api-testing')
        unauthorized_user.save()

        unauthorized_user.user_permissions.add(*Permission.objects.all())
        remove_perm_from_user(unauthorized_user, 'testruns.add_testcaserun')

        rpc_client = TCMSXmlrpc(unauthorized_user.username,
                                'api-testing',
                                '%s/xml-rpc/' % self.live_server_url).server

        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            rpc_client.TestRun.add_case(self.test_run.pk, self.test_case.pk)

        exists = TestCaseRun.objects.filter(run=self.test_run.pk, case=self.test_case.pk).exists()
        self.assertFalse(exists)


class TestAddTag(XmlrpcAPIBaseTest):
    def _fixture_setup(self):
        super(TestAddTag, self)._fixture_setup()

        self.product = ProductFactory()
        self.version = VersionFactory()
        self.build = self.product.build.first()
        self.plan = TestPlanFactory(author=self.api_user, product=self.product)

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

        unauthorized_user.user_permissions.add(*Permission.objects.all())
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
        self.build = self.product.build.first()
        self.plan = TestPlanFactory(author=self.api_user, product=self.product)

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

        unauthorized_user.user_permissions.add(*Permission.objects.all())
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


class TestUpdateTestRun(XmlrpcAPIBaseTest):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.test_run = TestRunFactory()

        self.updated_test_plan = TestPlanFactory()
        self.updated_build = BuildFactory()
        self.updated_summary = 'Updated summary.'
        self.updated_stop_date = datetime.strptime('2020-05-05', '%Y-%m-%d')

    def test_successful_update(self):
        update_fields = {
            'plan': self.updated_test_plan.pk,
            'build': self.updated_build.pk,
            'summary': self.updated_summary,
            'stop_date': self.updated_stop_date
        }

        # assert test plan is not already updated
        self.assertNotEqual(self.updated_test_plan, self.test_run.plan.name)
        self.assertNotEqual(self.updated_build, self.test_run.build.name)
        self.assertNotEqual(self.updated_summary, self.test_run.summary)
        self.assertNotEqual(self.updated_stop_date, self.test_run.stop_date)

        updated_test_run = self.rpc_client.exec.TestRun.update(self.test_run.pk, update_fields)
        self.test_run.refresh_from_db()

        # compare result, returned from API call with test run from DB
        self.assertEqual(updated_test_run['plan'], self.test_run.plan.name)
        self.assertEqual(updated_test_run['build'], self.test_run.build.name)
        self.assertEqual(updated_test_run['summary'], self.test_run.summary)
        self.assertEqual(updated_test_run['stop_date'], str(self.test_run.stop_date))

        # compare result, returned from API call with params sent to the API
        self.assertEqual(updated_test_run['plan'], self.updated_test_plan.name)
        self.assertEqual(updated_test_run['build'], self.updated_build.name)
        self.assertEqual(updated_test_run['summary'], self.updated_summary)
        self.assertEqual(updated_test_run['stop_date'], str(self.updated_stop_date))

    def test_wrong_date_format(self):
        test_run = TestRunFactory()
        update_fields = {
            'plan': self.updated_test_plan.pk,
            'build': self.updated_build.pk,
            'summary': self.updated_summary,
            'stop_date': '10-10-2010'
        }

        with self.assertRaisesMessage(Exception,
                                      'The stop date is invalid. The valid format is YYYY-MM-DD.'):
            self.rpc_client.exec.TestRun.update(test_run.pk, update_fields)

        # assert test run fields have not been updated
        test_run.refresh_from_db()
        self.assertNotEqual(update_fields['plan'], test_run.plan.pk)
        self.assertNotEqual(update_fields['build'], test_run.build.pk)
        self.assertNotEqual(update_fields['summary'], test_run.summary)
        self.assertNotEqual(datetime.strptime(update_fields['stop_date'], '%d-%m-%Y'),
                            test_run.stop_date)
