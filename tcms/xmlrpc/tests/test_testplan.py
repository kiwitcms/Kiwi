# -*- coding: utf-8 -*-

from xmlrpc.client import Fault as XmlRPCFault

from tcms.testcases.models import TestCase
from tcms.testcases.models import TestCasePlan
from tcms.testplans.models import TestPlan
from tcms.testplans.models import TCMSEnvPlanMap

from tcms.tests.factories import ComponentFactory
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
        self.case_1 = TestCaseFactory(author=self.tester,
                                      default_tester=None,
                                      reviewer=self.tester,
                                      plan=[self.plan_1])
        self.case_2 = TestCaseFactory(author=self.tester,
                                      default_tester=None,
                                      reviewer=self.tester,
                                      plan=[self.plan_1])

    def test_filter_plans(self):
        plans = self.rpc_client.TestPlan.filter({'pk__in': [self.plan_1.pk, self.plan_2.pk]})
        plan = plans[0]
        self.assertEqual(self.plan_1.name, plan['name'])
        self.assertEqual(self.plan_1.product_version.pk, plan['product_version_id'])
        self.assertEqual(self.plan_1.author.pk, plan['author_id'])

        self.assertEqual(2, len(plan['case']))
        self.assertIn(self.case_1.pk, plan['case'])
        self.assertIn(self.case_2.pk, plan['case'])
        self.assertEqual(0, len(plans[1]['case']))

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


class TestAddComponent(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestAddComponent, self)._fixture_setup()

        self.product = ProductFactory()
        self.plans = [
            TestPlanFactory(author=self.api_user, owner=self.api_user, product=self.product),
            TestPlanFactory(author=self.api_user, owner=self.api_user, product=self.product),
        ]
        self.component1 = ComponentFactory(name='xmlrpc test component 1',
                                           description='xmlrpc test description',
                                           product=self.product,
                                           initial_owner=None,
                                           initial_qa_contact=None)
        self.component2 = ComponentFactory(name='xmlrpc test component 2',
                                           description='xmlrpc test description',
                                           product=self.product,
                                           initial_owner=None,
                                           initial_qa_contact=None)

    def test_single_id(self):
        self.rpc_client.TestPlan.add_component(self.plans[0].pk, self.component1.pk)
        component_exists = TestPlan.objects.filter(
            pk=self.plans[0].pk, component__pk=self.component1.pk).exists()
        self.assertTrue(component_exists)

    def test_ids_in_array(self):
        plans_ids = [plan.pk for plan in self.plans]
        components_ids = [self.component1.pk, self.component2.pk]
        self.rpc_client.TestPlan.add_component(plans_ids, components_ids)
        for plan in TestPlan.objects.filter(pk__in=plans_ids):
            components_ids = [item.pk for item in plan.component.iterator()]
            self.assertTrue(self.component1.pk in components_ids)
            self.assertTrue(self.component2.pk in components_ids)


class TestPlanTypeMethods(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestPlanTypeMethods, self)._fixture_setup()

        self.plan_type = TestPlanTypeFactory(name='xmlrpc plan type', description='')

    def test_check_plan_type(self):
        result = self.rpc_client.TestPlan.check_plan_type(self.plan_type.name)
        self.assertEqual(self.plan_type.name, result['name'])
        self.assertEqual(self.plan_type.description, result['description'])
        self.assertEqual(self.plan_type.pk, result['id'])

    def test_get_plan_type(self):
        result = self.rpc_client.TestPlan.get_plan_type(self.plan_type.pk)
        self.assertEqual(self.plan_type.name, result['name'])
        self.assertEqual(self.plan_type.description, result['description'])
        self.assertEqual(self.plan_type.pk, result['id'])

        with self.assertRaisesRegex(XmlRPCFault, 'TestPlanType matching query does not exist'):
            self.rpc_client.TestPlan.get_plan_type(0)


class TestGetTestCases(XmlrpcAPIBaseTest):
    '''Test testplan.get_test_cases method'''

    def _fixture_setup(self):
        super(TestGetTestCases, self)._fixture_setup()

        self.tester = UserFactory(username='tester')
        self.reviewer = UserFactory(username='reviewer')
        self.product = ProductFactory()
        self.plan = TestPlanFactory(author=self.tester, owner=self.tester, product=self.product)
        self.cases = [
            TestCaseFactory(author=self.tester, default_tester=None, reviewer=self.reviewer,
                            plan=[self.plan]),
            TestCaseFactory(author=self.tester, default_tester=None, reviewer=self.reviewer,
                            plan=[self.plan]),
            TestCaseFactory(author=self.tester, default_tester=None, reviewer=self.reviewer,
                            plan=[self.plan]),
        ]
        self.another_plan = TestPlanFactory(
            author=self.tester,
            owner=self.tester,
            product=self.product
        )

    def test_get_test_cases(self):
        serialized_cases = self.rpc_client.TestPlan.get_test_cases(self.plan.pk)
        for case in serialized_cases:
            expected_case = TestCase.objects.get(plan=self.plan.pk, pk=case['case_id'])

            self.assertEqual(expected_case.summary, case['summary'])
            self.assertEqual(expected_case.priority_id, case['priority_id'])
            self.assertEqual(expected_case.author_id, case['author_id'])

            plan_case_rel = TestCasePlan.objects.get(plan=self.plan, case=case['case_id'])
            self.assertEqual(plan_case_rel.sortkey, case['sortkey'])

    def test_404_when_plan_nonexistent(self):
        with self.assertRaisesRegex(XmlRPCFault, 'TestPlan matching query does not exist'):
            self.rpc_client.TestPlan.get_test_cases(-1)

    def test_plan_has_no_cases(self):
        result = self.rpc_client.TestPlan.get_test_cases(self.another_plan.pk)
        self.assertEqual([], result)


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
        plans = self.rpc_client.TestPlan.update(self.plan_2.pk,
                                                {'env_group': self.env_group_2.pk})
        plan = plans[0]

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
