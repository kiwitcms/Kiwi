# -*- coding: utf-8 -*-

from xmlrpc.client import Fault as XmlRPCFault

from tcms.testplans.models import TestPlan
from tcms.testcases.models import TestCasePlan
from tcms.testplans.models import TCMSEnvPlanMap

from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestPlanTypeFactory
from tcms.tests.factories import TestTagFactory
from tcms.tests.factories import TCMSEnvGroupFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestFilter(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestFilter, self)._fixture_setup()

        self.product = ProductFactory()
        self.version = VersionFactory(product=self.product)
        self.tester = UserFactory()
        self.plan_type = TestPlanTypeFactory(name='manual smoking')
        self.plan_1 = TestPlanFactory(product_version=self.version,
                                      product=self.product,
                                      author=self.tester,
                                      type=self.plan_type)
        self.plan_2 = TestPlanFactory(product_version=self.version,
                                      product=self.product,
                                      author=self.tester,
                                      type=self.plan_type)

    def test_filter_plans(self):
        plans = self.rpc_client.TestPlan.filter({'pk__in': [self.plan_1.pk, self.plan_2.pk]})
        plan = plans[0]
        self.assertEqual(self.plan_1.name, plan['name'])
        self.assertEqual(self.plan_1.product_version.pk, plan['product_version_id'])
        self.assertEqual(self.plan_1.author.pk, plan['author_id'])

    def test_filter_out_all_plans(self):
        plans_total = TestPlan.objects.all().count()
        self.assertEqual(plans_total, len(self.rpc_client.TestPlan.filter()))
        self.assertEqual(plans_total, len(self.rpc_client.TestPlan.filter({})))


class TestAddTag(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestAddTag, self)._fixture_setup()

        self.product = ProductFactory()
        self.plans = [
            TestPlanFactory(author=self.api_user, owner=self.api_user, product=self.product),
            TestPlanFactory(author=self.api_user, owner=self.api_user, product=self.product),
        ]

        self.tag1 = TestTagFactory(name='xmlrpc_test_tag_1')
        self.tag2 = TestTagFactory(name='xmlrpc_test_tag_2')
        self.tag_name = 'xmlrpc_tag_name_1'

    def test_single_id(self):
        '''Test with single plan id and tag id'''
        with self.assertRaisesRegex(XmlRPCFault, 'Parameter tags must be a string'):
            self.rpc_client.TestPlan.add_tag(self.plans[0].pk, self.tag1.pk)

        self.rpc_client.TestPlan.add_tag(self.plans[0].pk, self.tag1.name)
        tag_exists = TestPlan.objects.filter(pk=self.plans[0].pk, tag__pk=self.tag1.pk).exists()
        self.assertTrue(tag_exists)

    def test_array_argument(self):
        self.rpc_client.TestPlan.add_tag(self.plans[0].pk, [self.tag2.name, self.tag_name])
        tag_exists = TestPlan.objects.filter(pk=self.plans[0].pk,
                                             tag__name__in=[self.tag2.name, self.tag_name])
        self.assertTrue(tag_exists.exists())

        plans_ids = [plan.pk for plan in self.plans]
        tags_names = [self.tag_name, 'xmlrpc_tag_name_2']
        self.rpc_client.TestPlan.add_tag(plans_ids, tags_names)
        for plan in self.plans:
            tag_exists = plan.tag.filter(name__in=tags_names).exists()
            self.assertTrue(tag_exists)


class TestRemoveTag(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestRemoveTag, self)._fixture_setup()

        self.product = ProductFactory()
        self.plans = [
            TestPlanFactory(author=self.api_user, owner=self.api_user, product=self.product),
            TestPlanFactory(author=self.api_user, owner=self.api_user, product=self.product),
        ]

        self.tag0 = TestTagFactory(name='xmlrpc_test_tag_0')
        self.tag1 = TestTagFactory(name='xmlrpc_test_tag_1')

        self.plans[0].add_tag(self.tag0)
        self.plans[1].add_tag(self.tag1)

        self.tag_name = 'xmlrpc_tag_name_1'

    def test_single_id(self):
        '''Test with single plan id and tag id'''
        # removing by ID raises an error
        with self.assertRaisesRegex(XmlRPCFault, 'Parameter tags must be a string'):
            self.rpc_client.TestPlan.remove_tag(self.plans[0].pk, self.tag0.pk)

        # removing by name works fine
        self.rpc_client.TestPlan.remove_tag(self.plans[0].pk, self.tag0.name)
        tag_exists = TestPlan.objects.filter(pk=self.plans[0].pk, tag__pk=self.tag0.pk).exists()
        self.assertFalse(tag_exists)

    def test_array_argument(self):
        self.rpc_client.TestPlan.remove_tag(self.plans[0].pk, [self.tag0.name, self.tag_name])
        tag_exists = TestPlan.objects.filter(pk=self.plans[0].pk,
                                             tag__name__in=[self.tag0.name, self.tag_name])
        self.assertFalse(tag_exists.exists())

        plans_ids = [plan.pk for plan in self.plans]
        tags_names = [self.tag_name, 'xmlrpc_tag_name_2']
        self.rpc_client.TestPlan.remove_tag(plans_ids, tags_names)
        for plan in self.plans:
            tag_exists = plan.tag.filter(name__in=tags_names).exists()
            self.assertFalse(tag_exists)


class TestUpdate(XmlrpcAPIBaseTest):
    """ Tests the XMLRPM testplan.update method """

    def _fixture_setup(self):
        super(TestUpdate, self)._fixture_setup()

        self.env_group_1 = TCMSEnvGroupFactory()
        self.env_group_2 = TCMSEnvGroupFactory()
        self.product = ProductFactory()
        self.version = VersionFactory(product=self.product)
        self.tester = UserFactory()
        self.plan_type = TestPlanTypeFactory(name='manual smoking')
        self.plan_1 = TestPlanFactory(product_version=self.version,
                                      product=self.product,
                                      author=self.tester,
                                      type=self.plan_type,
                                      env_group=(self.env_group_1,))
        self.plan_2 = TestPlanFactory(product_version=self.version,
                                      product=self.product,
                                      author=self.tester,
                                      type=self.plan_type,
                                      env_group=(self.env_group_1,))

    def test_update_env_group(self):
        # plan_1 and plan_2 point to self.env_group_1
        # and there are only 2 objects in the many-to-many table
        # so we issue XMLRPC request to modify the env_group of self.plan_2
        plan = self.rpc_client.TestPlan.update(self.plan_2.pk,
                                               {'env_group': self.env_group_2.pk})

        # now verify that the returned TP (plan_2) has been updated to env_group_2
        self.assertEqual(self.plan_2.pk, plan['plan_id'])
        self.assertEqual(1, len(plan['env_group']))
        self.assertEqual(self.env_group_2.pk, plan['env_group'][0])

        # and that plan_1 has not changed at all
        self.assertEqual(1, self.plan_1.env_group.count())
        self.assertEqual(self.env_group_1.pk, self.plan_1.env_group.all()[0].pk)

        # and there are still only 2 objects in the many-to-many table
        # iow no dangling objects left
        self.assertEqual(2, TCMSEnvPlanMap.objects.filter(plan__in=[self.plan_1,
                                                                    self.plan_2]).count())

    def test_update_text(self):
        self.assertIsNone(self.plan_1.latest_text())
        self.rpc_client.TestPlan.update(self.plan_1.pk, {'text': 'This has been updated'})
        # reload from db
        self.plan_1.refresh_from_db()
        # assert
        self.assertEqual('This has been updated', self.plan_1.latest_text().plan_text)


class TestRemoveCase(XmlrpcAPIBaseTest):
    """ Test the XML-RPC method TestPlan.remove_case() """

    def _fixture_setup(self):
        super(TestRemoveCase, self)._fixture_setup()
        self.testcase_1 = TestCaseFactory()
        self.testcase_2 = TestCaseFactory()
        self.plan_1 = TestPlanFactory()
        self.plan_2 = TestPlanFactory()

        self.testcase_1.add_to_plan(self.plan_1)

        self.testcase_2.add_to_plan(self.plan_1)
        self.testcase_2.add_to_plan(self.plan_2)

    def test_remove_case_with_single_plan(self):
        self.rpc_client.TestPlan.remove_case(self.plan_1.pk, self.testcase_1.pk)
        self.assertEqual(0, self.testcase_1.plan.count())

    def test_remove_case_with_two_plans(self):
        self.assertEqual(2, self.testcase_2.plan.count())

        self.rpc_client.TestPlan.remove_case(self.plan_1.pk, self.testcase_2.pk)
        self.assertEqual(1, self.testcase_2.plan.count())


class TestAddCase(XmlrpcAPIBaseTest):
    """ Test the XML-RPC method TestPlan.add_case() """

    def _fixture_setup(self):
        super(TestAddCase, self)._fixture_setup()

        self.testcase_1 = TestCaseFactory()
        self.testcase_2 = TestCaseFactory()
        self.testcase_3 = TestCaseFactory()

        self.plan_1 = TestPlanFactory()
        self.plan_2 = TestPlanFactory()
        self.plan_3 = TestPlanFactory()

        # case 1 is already linked to plan 1
        self.testcase_1.add_to_plan(self.plan_1)

    def test_ignores_existing_mappings(self):
        plans = [self.plan_1.pk, self.plan_2.pk, self.plan_3.pk]
        cases = [self.testcase_1.pk, self.testcase_2.pk, self.testcase_3.pk]

        for plan_id in plans:
            for case_id in cases:
                self.rpc_client.TestPlan.add_case(plan_id, case_id)

        # no duplicates for plan1/case1 were created
        self.assertEqual(
            1,
            TestCasePlan.objects.filter(
                plan=self.plan_1.pk,
                case=self.testcase_1.pk
            ).count()
        )

        # verify all case/plan combinations exist
        for plan_id in plans:
            for case_id in cases:
                self.assertEqual(
                    1,
                    TestCasePlan.objects.filter(
                        plan=plan_id,
                        case=case_id
                    ).count()
                )
