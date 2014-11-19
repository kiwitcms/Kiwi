# -*- coding: utf-8 -*-

from django_nose.testcases import FastFixtureTestCase

from tcms.management.models import Product
from tcms.management.models import TestBuild
from tcms.testcases.models import TestCase
from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestCaseRun
from tcms.testruns.models import TestRun
from tcms.xmlrpc.serializer import ProductXMLRPCSerializer
from tcms.xmlrpc.serializer import TestBuildXMLRPCSerializer
from tcms.xmlrpc.serializer import TestCaseRunXMLRPCSerializer
from tcms.xmlrpc.serializer import TestCaseXMLRPCSerializer
from tcms.xmlrpc.serializer import TestPlanXMLRPCSerializer
from tcms.xmlrpc.serializer import TestRunXMLRPCSerializer
from tcms.xmlrpc.serializer import XMLRPCSerializer


__all__ = ('TestSerializationBackwardCompatibility',)


serializers_classes = {
    Product: ProductXMLRPCSerializer,
    TestBuild: TestBuildXMLRPCSerializer,
    TestCase: TestCaseXMLRPCSerializer,
    TestCaseRun: TestCaseRunXMLRPCSerializer,
    TestPlan: TestPlanXMLRPCSerializer,
    TestRun: TestRunXMLRPCSerializer,
}


def remove_alias_extra_fields(model_class, serialize_result):
    '''Have to remove extra fields, these are unnecessary for this test'''

    serializer_class = serializers_classes[model_class]

    if not hasattr(serializer_class, 'extra_fields'):
        return

    if 'alias' not in serializer_class.extra_fields:
        return

    alias_fields = serializer_class.extra_fields['alias']
    for original_name, mapped_name in alias_fields.iteritems():
        del serialize_result[mapped_name]


class TestSerializationBackwardCompatibility(FastFixtureTestCase):
    '''Ensure new serialization method to generate same data with original

    Remove this test when migrate to new serialization completely.
    '''

    fixtures = ['unittest.json']

    def _test_backward_compatible(self, model_class, object_pk):
        '''Ensure new serialization method to generate same data'''

        base_object = model_class.objects.get(pk=object_pk)
        sample_result = model_class.to_xmlrpc(query={'pk': object_pk})[0]
        remove_alias_extra_fields(model_class, sample_result)
        base_result = XMLRPCSerializer(model=base_object).serialize_model()

        sample_fields = [name for name in sample_result.keys()]
        base_fields = [name for name in base_result.keys()]

        # Ensure fields are same.
        test_result = list(set(sample_fields) - set(base_fields))
        self.assertEqual(test_result, [])
        test_result = list(set(base_fields) - set(sample_fields))
        self.assertEqual(test_result, [])

        # Ensure values are same.
        for sample_field, sample_value in sample_result.iteritems():
            self.assertEqual(sample_value, base_result[sample_field])

    def test_testplan(self):
        plan = TestPlan.objects.all()[:1]
        self._test_backward_compatible(TestPlan, plan[0].pk)

    def test_testcase(self):
        case = TestCase.objects.all()[:1]
        self._test_backward_compatible(TestCase, case[0].pk)

    def test_testrun(self):
        run = TestRun.objects.all()[:1]
        self._test_backward_compatible(TestRun, run[0].pk)

    def test_testcaserun(self):
        case_run = TestCaseRun.objects.all()[:1]
        self._test_backward_compatible(TestCaseRun, case_run[0].pk)

    def test_testbuild(self):
        build = TestBuild.objects.all()[:1]
        self._test_backward_compatible(TestBuild, build[0].pk)

    def test_product(self):
        product = Product.objects.all()[:1]
        self._test_backward_compatible(Product, product[0].pk)
