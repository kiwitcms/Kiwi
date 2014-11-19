# -*- coding: utf-8 -*-

import unittest

from django_nose.testcases import FastFixtureTestCase

from tcms.management.models import Product
from tcms.testcases.models import TestCase
from tcms.testplans.models import TestPlan
from tcms.xmlrpc.serializer import QuerySetBasedXMLRPCSerializer
from tcms.xmlrpc.serializer import XMLRPCSerializer
from tcms.xmlrpc.serializer import datetime_to_str
from tcms.xmlrpc.serializer import do_nothing
from tcms.xmlrpc.serializer import encode_utf8
from tcms.xmlrpc.serializer import to_str


class TestXMLSerializer(FastFixtureTestCase):

    fixtures = ['unittest.json']

    def setUp(self):
        self.testcase = TestCase.objects.all()[0]

    def test_serializer(self):
        serializer = XMLRPCSerializer(model=self.testcase)

        result = serializer.serialize_model()

        self.assertEqual(self.testcase.category.pk, result['category_id'])
        self.assertEqual(str(self.testcase.category), result['category'])

        component_pks = [c.pk for c in self.testcase.component.all()]
        component_pks.sort()
        result['component'].sort()
        self.assertEqual(component_pks, result['component'])

        self.assertEqual(self.testcase.alias, result['alias'])
        self.assertEqual(self.testcase.arguments, result['arguments'])


#################### Mock serializer classes for testing ####################


class MockTestPlanSerializer(QuerySetBasedXMLRPCSerializer):
    values_fields_mapping = {
        'create_date': ('create_date', datetime_to_str),
        'extra_link': ('extra_link', do_nothing),
        'is_active': ('is_active', do_nothing),
        'name': ('name', do_nothing),
        'plan_id': ('plan_id', do_nothing),

        'author': ('author_id', do_nothing),
        'author__username': ('author', to_str),
        'product_version': ('product_version_id', do_nothing),
        'product_version__value': ('product_version', encode_utf8),
    }

    extra_fields = {
        'alias': {'product_version': 'default_product_version'},
    }

    m2m_fields = ('attachment', 'case')


class MockTestCaseSerializer(QuerySetBasedXMLRPCSerializer):
    primary_key = 'case_id'

    values_fields_mapping = {
        'alias': ('alias', do_nothing),
        'arguments': ('arguments', do_nothing),
        'case_id': ('case_id', do_nothing),
        'create_date': ('create_date', datetime_to_str),

        'author': ('author_id', do_nothing),
        'author__username': ('author', to_str),
        'case_status': ('case_status_id', do_nothing),
        'case_status__name': ('case_status', encode_utf8),
    }


class MockProductSerializer(QuerySetBasedXMLRPCSerializer):
    '''Empty definition to test some method's default behavior'''


#################### Mock serializer classes for testing ####################


class TestQuerySetBasedSerializer(FastFixtureTestCase):
    '''Test QuerySetBasedXMLRPCSerializer'''

    fixtures = ['unittest.json']

    def setUp(self):
        self.plans = TestPlan.objects.all()
        self.plan_serializer = MockTestPlanSerializer(TestPlan, self.plans)

        self.cases = TestCase.objects.all()
        self.case_serializer = MockTestCaseSerializer(TestCase, self.cases)

        self.products = Product.objects.all()
        self.product_serializer = MockProductSerializer(Product, self.products)

    def test_get_values_fields_mapping(self):
        mapping = self.product_serializer._get_values_fields_mapping()
        self.assertEqual(mapping, {})

        mapping = self.case_serializer._get_values_fields_mapping()
        self.assertEqual(mapping, MockTestCaseSerializer.values_fields_mapping)

    def test_get_values_fields(self):
        fields = self.case_serializer._get_values_fields()
        fields.sort()
        expected_fields = MockTestCaseSerializer.values_fields_mapping.keys()
        expected_fields.sort()
        self.assertEqual(expected_fields, fields)

        fields = self.product_serializer._get_values_fields()
        fields.sort()
        expected_fields = [field.name for field in Product._meta.fields]
        expected_fields.sort()
        self.assertEqual(expected_fields, fields)

    def test_get_m2m_fields(self):
        fields = list(self.plan_serializer._get_m2m_fields())
        fields.sort()
        expected_fields = list(MockTestPlanSerializer.m2m_fields)
        expected_fields.sort()
        self.assertEqual(expected_fields, fields)

        fields = list(self.case_serializer._get_m2m_fields())
        fields.sort()
        expected_fields = [field.name for field in
                           TestCase._meta._many_to_many()]
        expected_fields.sort()
        self.assertEqual(expected_fields, fields)

        fields = self.product_serializer._get_m2m_fields()
        expected_fields = tuple(field.name for field in
                                Product._meta._many_to_many())
        self.assertEqual(fields, ())
        self.assertEqual(expected_fields, fields)

    def test_get_primary_key_field(self):
        field_name = self.case_serializer._get_primary_key_field()
        self.assertEqual(field_name, MockTestCaseSerializer.primary_key)

        field_name = self.plan_serializer._get_primary_key_field()
        expected_field_name = [field.name for field in TestPlan._meta.fields
                               if field.primary_key][0]
        self.assertEqual(expected_field_name, field_name)

    def verify_m2m_field_query_result(self, m2m_field_name, result):
        for object_pk, objects in result.iteritems():
            self.assert_(isinstance(objects, tuple))
            for object_value in objects:
                self.assertEqual(object_pk, object_value['pk'])
                self.assert_(m2m_field_name in object_value)

    def test_query_m2m_field(self):
        m2m_field_name = 'case'
        result = self.plan_serializer._query_m2m_field(m2m_field_name)

        self.assertEqual(len(result), len(self.plans),
                         'There are cases in database, but not serialized.')
        self.verify_m2m_field_query_result(m2m_field_name, result)

    def test_query_m2m_fields(self):
        result = self.plan_serializer._query_m2m_fields()
        self.assert_(isinstance(result, dict))
        self.assertEqual(len(result), len(MockTestPlanSerializer.m2m_fields))

        for m2m_field_name, this_query_result in result.iteritems():
            self.assert_(m2m_field_name in MockTestPlanSerializer.m2m_fields)
            self.assert_(isinstance(this_query_result, dict))

            # Method to verify object_values is same with test case
            # test_query_m2m_field
            self.verify_m2m_field_query_result(m2m_field_name,
                                               this_query_result)

    def test_get_related_object_pks(self):
        m2m_field_name = 'case'
        m2m_query_result = self.plan_serializer._query_m2m_fields()
        func = self.plan_serializer._get_related_object_pks
        result = list(func(m2m_query_result, self.plans[0].pk, m2m_field_name))
        result.sort()

        expected_values = [row['case'] for row in
                           self.plans.values('pk', 'case').iterator()
                           if row['case']]
        expected_values.sort()
        self.assertEqual(expected_values, result)

    ######## Test cases for extra_fields #######

    def test_get_extra_fields(self):
        extra_fields = self.plan_serializer.get_extra_fields()
        self.assertNotEqual(extra_fields, {})
        self.assert_('alias' in extra_fields)

        extra_fields = self.case_serializer.get_extra_fields()
        self.assertEqual(extra_fields, {})

    def test_handle_extra_fields_alias(self):
        serialize_result = {'plan_id': 1000, 'product_version': 1}
        test_data = serialize_result.copy()
        self.plan_serializer._handle_extra_fields(test_data)
        self.assert_('default_product_version' in test_data)
        self.assertEqual(test_data['default_product_version'],
                         serialize_result['product_version'])
        self.assertEqual(test_data['plan_id'], serialize_result['plan_id'])
        self.assertEqual(test_data['product_version'],
                         serialize_result['product_version'])

        test_data = serialize_result.copy()
        self.case_serializer._handle_extra_fields(test_data)
        self.assertEqual(test_data, serialize_result)

    ######## Test cases for core serialization method #######

    def test_serialize_queryset(self):
        serialize_result = self.plan_serializer.serialize_queryset()
        self.assertEqual(len(self.plans), len(serialize_result))

        for plan in serialize_result:
            plan_id = plan['plan_id']
            expected_plan = TestPlan.objects.get(pk=plan_id)
            self.assertEqual(expected_plan.name, plan['name'])
            self.assertEqual(expected_plan.is_active, plan['is_active'])
            self.assertEqual(expected_plan.extra_link, plan['extra_link'])
            self.assertEqual(datetime_to_str(expected_plan.create_date),
                             plan['create_date'])
            self.assertEqual(expected_plan.author_id, plan['author_id'])
            self.assertEqual(expected_plan.author.username, plan['author'])
            self.assertEqual(expected_plan.product_version_id,
                             plan['product_version_id'])
            self.assertEqual(expected_plan.product_version.value,
                             plan['product_version'])

    def test_serialize_queryset_with_empty_querset(self):
        cases = self.cases.filter(pk__lt=0)
        serializer = MockTestCaseSerializer(TestCase, cases)
        result = serializer.serialize_queryset()
        self.assert_(len(result) == 0)


class TestUtilityMethods(unittest.TestCase):

    def test_datetime_to_str(self):
        value = datetime_to_str(None)
        self.assertEqual(value, None)

        from datetime import datetime
        now = datetime.now()
        value = datetime_to_str(now)
        expected_value = datetime.strftime(now, '%Y-%m-%d %H:%M:%S')
        self.assertEqual(expected_value, value)
