# -*- coding: utf-8 -*-

import unittest

from xmlrpclib import Fault

from django.conf import settings
from django.contrib.auth.models import User

from django_nose.testcases import FastFixtureTestCase

from tcms.core.contrib.xml2dict.xml2dict import XML2Dict
from tcms.management.models import Component
from tcms.management.models import Priority
from tcms.management.models import Product
from tcms.management.models import TestTag
from tcms.management.models import Version
from tcms.testcases.models import TestCase
from tcms.testcases.models import TestCasePlan
from tcms.testcases.models import TestCaseStatus
from tcms.testplans.models import TestPlan
from tcms.testplans.models import TestPlanComponent
from tcms.testplans.models import TestPlanTag
from tcms.testplans.models import TestPlanType
from tcms.xmlrpc.api import testplan as XmlrpcTestPlan
from tcms.xmlrpc.api.testplan import clean_xml_file
from tcms.xmlrpc.api.testplan import process_case
from tcms.xmlrpc.tests.utils import make_http_request
from tcms.xmlrpc.tests.utils import user_should_have_perm

__all__ = (
    'TestAddComponent',
    'TestAddTag',
    'TestCleanXMLFile',
    'TestComponentMethods',
    'TestGetAllCasesTags',
    'TestGetProduct',
    'TestGetTestCases',
    'TestGetTestRuns',
    'TestGetText',
    'TestImportCaseViaXML',
    'TestPlanTypeMethods',
    'TestRemoveTag',
    'TestTestPlan',
    'TestUpdate',
)


class TestAddTag(FastFixtureTestCase):

    fixtures = ['unittest.json']

    def setUp(self):
        self.http_req = make_http_request()
        user_should_have_perm(self.http_req.user, 'testplans.add_testplantag')

        self.plans = TestPlan.objects.all()[:2]
        self.tag1 = TestTag.objects.create(name='xmlrpc_test_tag_1')
        self.tag2 = TestTag.objects.create(name='xmlrpc_test_tag_2')
        self.tag_name = 'xmlrpc_tag_name_1'

    def tearDown(self):
        tags = [self.tag1.pk, self.tag2.pk]
        for plan in self.plans:
            TestPlanTag.objects.filter(plan=plan, tag__in=tags).delete()
        self.tag1.delete()
        self.tag2.delete()

    def test_single_id(self):
        '''Test with singal plan id and tag id'''
        try:
            XmlrpcTestPlan.add_tag(self.http_req,
                                   self.plans[0].pk, self.tag1.pk)
        except Fault as e:
            self.assertEqual(e.faultCode, 500)
        else:
            self.fail('Argument tags accepts values of string and array ' +
                      'only. Passing a number should cause it fail.')

        XmlrpcTestPlan.add_tag(self.http_req,
                               self.plans[0].pk, self.tag1.name)
        tag_exists = TestPlan.objects.filter(pk=self.plans[0].pk,
                                             tag__pk=self.tag1.pk).exists()
        self.assert_(tag_exists)

    def test_array_argument(self):
        XmlrpcTestPlan.add_tag(self.http_req,
                               self.plans[0].pk,
                               [self.tag2.name, self.tag_name])
        tag_exists = TestPlan.objects.filter(
            pk=self.plans[0].pk,
            tag__name__in=[self.tag2.name, self.tag_name])
        self.assert_(tag_exists.exists())

        plans_ids = [plan.pk for plan in self.plans]
        tags_names = [self.tag_name, 'xmlrpc_tag_name_2']
        XmlrpcTestPlan.add_tag(self.http_req, plans_ids, tags_names)
        for plan in self.plans:
            tag_exists = plan.tag.filter(name__in=tags_names).exists()
            self.assert_(tag_exists)


class TestAddComponent(FastFixtureTestCase):

    fixtures = ['unittest.json']

    def setUp(self):
        self.http_req = make_http_request()
        perm_name = 'testplans.add_testplancomponent'
        user_should_have_perm(self.http_req.user, perm_name)

        self.product = Product.objects.all()[0]
        self.plans = TestPlan.objects.all()[:2]
        self.component1 = Component.objects.create(
            name='xmlrpc test component 1',
            description='xmlrpc test description',
            product=self.product)
        self.component2 = Component.objects.create(
            name='xmlrpc test component 2',
            description='xmlrpc test description',
            product=self.product)

    def tearDown(self):
        components = [self.component1.pk, self.component2.pk]
        for plan in self.plans:
            TestPlanComponent.objects.filter(plan=plan,
                                             component__in=components).delete()
        self.component1.delete()
        self.component2.delete()

    def test_single_id(self):
        XmlrpcTestPlan.add_component(self.http_req,
                                     self.plans[0].pk, self.component1.pk)
        component_exists = TestPlan.objects.filter(
            pk=self.plans[0].pk, component__pk=self.component1.pk).exists()
        self.assert_(component_exists)

    def test_ids_in_array(self):
        try:
            XmlrpcTestPlan.add_component(self.http_req, [1, 2])
        except Fault as e:
            self.assertEqual(e.faultCode, 400)

        plans_ids = [plan.pk for plan in self.plans]
        components_ids = [self.component1.pk, self.component2.pk]
        XmlrpcTestPlan.add_component(self.http_req, plans_ids, components_ids)
        for plan in TestPlan.objects.filter(pk__in=plans_ids):
            components_ids = [item.pk for item in plan.component.iterator()]
            self.assert_(self.component1.pk in components_ids)
            self.assert_(self.component2.pk in components_ids)


class TestPlanTypeMethods(unittest.TestCase):

    def setUp(self):
        self.http_req = make_http_request()
        self.plan_type = TestPlanType.objects.create(name='xmlrpc plan type',
                                                     description='')

    def tearDown(self):
        self.plan_type.delete()

    def test_check_plan_type(self):
        try:
            XmlrpcTestPlan.check_plan_type(self.http_req)
        except Fault as e:
            self.assertEqual(e.faultCode, 400)

        result = XmlrpcTestPlan.check_plan_type(self.http_req,
                                                self.plan_type.name)
        self.assertEqual(self.plan_type.name, result['name'])
        self.assertEqual(self.plan_type.description, result['description'])
        self.assertEqual(self.plan_type.pk, result['id'])

    def test_get_plan_type(self):
        result = XmlrpcTestPlan.get_plan_type(self.http_req, self.plan_type.pk)
        self.assertEqual(self.plan_type.name, result['name'])
        self.assertEqual(self.plan_type.description, result['description'])
        self.assertEqual(self.plan_type.pk, result['id'])

        try:
            result = XmlrpcTestPlan.get_plan_type(self.http_req, 0)
        except Fault as e:
            self.assertEqual(404, e.faultCode)

        try:
            result = XmlrpcTestPlan.get_plan_type(self.http_req, -2)
        except Fault as e:
            self.assertEqual(404, e.faultCode)


class TestGetProduct(FastFixtureTestCase):

    fixtures = ['unittest.json']

    def setUp(self):
        self.http_req = make_http_request()
        self.plan = TestPlan.objects.all()[:1][0]

    def _verify_serialize_result(self, result):
        self.assertEqual(self.plan.product.name, result['name'])
        self.assertEqual(self.plan.product.description, result['description'])
        self.assertEqual(self.plan.product.disallow_new, result['disallow_new'])
        self.assertEqual(self.plan.product.vote_super_user,
                         result['vote_super_user'])
        self.assertEqual(self.plan.product.max_vote_super_bug,
                         result['max_vote_super_bug'])
        self.assertEqual(self.plan.product.votes_to_confirm,
                         result['votes_to_confirm'])
        self.assertEqual(self.plan.product.default_milestone,
                         result['default_milestone'])
        self.assertEqual(self.plan.product.classification.pk,
                         result['classification_id'])
        self.assertEqual(self.plan.product.classification.name,
                         result['classification'])

    def test_get_product(self):
        try:
            XmlrpcTestPlan.get_product(self.http_req, 0)
            self.fail('Passing 0 should cause 404 error due to it does not ' +
                      'exist.')
        except Fault as e:
            self.assertEqual(404, e.faultCode)

        result = XmlrpcTestPlan.get_product(self.http_req, str(self.plan.pk))
        self._verify_serialize_result(result)

        result = XmlrpcTestPlan.get_product(self.http_req, self.plan.pk)
        self._verify_serialize_result(result)

        try:
            XmlrpcTestPlan.get_product(self.http_req, 'plan_id')
        except Fault as e:
            self.assertEqual(400, e.faultCode)


class TestComponentMethods(FastFixtureTestCase):
    '''TODO: '''

    fixtures = ['unittest.json']

    def setUp(self):
        self.http_req = make_http_request()

    def tearDown(self):
        pass


class TestGetAllCasesTags(FastFixtureTestCase):
    '''TODO: '''


class TestGetTestCases(FastFixtureTestCase):
    '''Test testplan.get_test_cases method'''

    fixtures = ['unittest.json']

    def setUp(self):
        self.http_req = make_http_request()
        self.plan = TestPlan.objects.all()[:1][0]

        self.product = Product.objects.all()[:1][0]
        self.version = Version.objects.create(value='testing',
                                              product=self.product)
        self.plan_type = TestPlanType.objects.all()[:1][0]
        self.new_plan = TestPlan.objects.create(
            name='new test plan',
            product_version=self.version,
            owner=self.http_req.user,
            author=self.http_req.user,
            product=self.product,
            type=self.plan_type,
            parent=None)

    def tearDown(self):
        self.new_plan.delete()
        self.version.delete()

    def test_get_test_cases(self):
        serialized_cases = XmlrpcTestPlan.get_test_cases(self.http_req,
                                                         self.plan.pk)
        for case in serialized_cases:
            expected_case = TestCase.objects.filter(
                plan=self.plan.pk).get(pk=case['case_id'])

            self.assertEqual(expected_case.summary, case['summary'])
            self.assertEqual(expected_case.priority_id, case['priority_id'])
            self.assertEqual(expected_case.author_id, case['author_id'])

            plan_case_rel = TestCasePlan.objects.get(plan=self.plan,
                                                     case=case['case_id'])
            self.assertEqual(plan_case_rel.sortkey, case['sortkey'])

    def test_different_argument_type(self):
        try:
            XmlrpcTestPlan.get_test_cases(self.http_req, str(self.plan.pk))
        except Fault as e:
            self.assertEqual(400, e.faultCode)

    def test_404_when_plan_nonexistent(self):
        try:
            XmlrpcTestPlan.get_test_cases(self.http_req, 0)
        except Fault as e:
            self.assertEqual(404, e.faultCode)

        plan_id = TestPlan.objects.order_by('-pk')[:1][0].pk + 1
        try:
            XmlrpcTestPlan.get_test_cases(self.http_req, plan_id)
        except Fault as e:
            self.assertEqual(404, e.faultCode)

    def test_plan_has_no_cases(self):
        result = XmlrpcTestPlan.get_test_cases(self.http_req, self.new_plan.pk)
        self.assertEqual([], result)


class TestGetTestRuns(FastFixtureTestCase):
    '''TODO: '''


class TestGetText(FastFixtureTestCase):
    '''TODO: '''


class TestRemoveTag(FastFixtureTestCase):
    '''TODO: '''


class TestImportCaseViaXML(FastFixtureTestCase):
    '''TODO: '''


class TestUpdate(FastFixtureTestCase):
    '''TODO: '''


# ################ Section for testing testplan.import_case_via_XML ########

xml_single_case = '''
<testcase author="%(author)s" priority="%(priority)s"
          automated="%(automated)s" status="%(status)s">
    <summary>%(summary)s</summary>
    <categoryname>%(categoryname)s</categoryname>
    <defaulttester>%(defaulttester)s</defaulttester>
    <notes>%(notes)s</notes>
    <action>%(action)s</action>
    <expectedresults>%(expectedresults)s</expectedresults>
    <setup>%(setup)s</setup>
    <breakdown>%(breakdown)s</breakdown>
    %(tags)s
</testcase>'''


sample_case_data = {
    'author': 'user@example.com',
    'priority': 'P1',
    'automated': '0',
    'status': 'CONFIRMED',
    'summary': 'test case',
    'categoryname': '--default--',
    'defaulttester': '',
    'notes': '',
    'action': '',
    'expectedresults': '',
    'setup': '',
    'effect': '',
    'breakdown': '',
    'tag': ['tag 1'],
}


xml_file_without_error = u'''
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<!DOCTYPE testopia SYSTEM "testopia.dtd" [
  <!ENTITY testopia_lt "<">
  <!ENTITY testopia_gt ">">
]>
<testopia version="1.1">
  <testcase author="user@example.com" priority="P1"
      automated="0" status="CONFIRMED">
    <summary>测试用例</summary>
    <categoryname>--default--</categoryname>
    <defaulttester></defaulttester>
    <notes>&lt;script type=&quot;text/javascript&quot;&gt;
    alert(&quot;Exploited!&quot;);
    &lt;/script&gt;</notes>
    <action></action>
    <expectedresults></expectedresults>
    <setup></setup>
    <breakdown></breakdown>
    <tag>haha &lt;script&gt;alert(&#39;HAHAHA&#39;)&lt;/script&gt;</tag>
  </testcase>
  <testcase author="user@example.com" priority="P1"
      automated="0" status="CONFIRMED">
    <summary>case 2</summary>
    <categoryname>--default--</categoryname>
    <defaulttester></defaulttester>
    <notes></notes>
    <action></action>
    <expectedresults></expectedresults>
    <setup></setup>
    <breakdown></breakdown>
    <tag>xmlrpc</tag>
    <tag>haha</tag>
    <tag>case management system</tag>
  </testcase>
</testopia>
'''


xml_file_single_case_without_error = u'''
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<!DOCTYPE testopia SYSTEM "testopia.dtd" [
  <!ENTITY testopia_lt "<">
  <!ENTITY testopia_gt ">">
]>
<testopia version="1.1">
  <testcase author="user@example.com" priority="P1"
      automated="0" status="CONFIRMED">
    <summary>case 1</summary>
    <categoryname>--default--</categoryname>
    <defaulttester></defaulttester>
    <notes>&lt;script type=&quot;text/javascript&quot;&gt;
    alert(&quot;Exploited!&quot;);
    &lt;/script&gt;</notes>
    <action></action>
    <expectedresults></expectedresults>
    <setup></setup>
    <breakdown></breakdown>
    <tag>haha &lt;script&gt;alert(&#39;HAHAHA&#39;)&lt;/script&gt;</tag>
  </testcase>
</testopia>
'''


# With error, non-existent priority and defaulttester's email
xml_file_with_error = u'''
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<!DOCTYPE testopia SYSTEM "testopia.dtd" [
  <!ENTITY testopia_lt "<">
  <!ENTITY testopia_gt ">">
]>
<testopia version="1.1">
  <testcase author="user@example.com" priority="Pn"
      automated="0" status="CONFIRMED">
    <summary>case 2</summary>
    <categoryname>--default--</categoryname>
    <defaulttester>x-man@universe.net</defaulttester>
    <notes></notes>
    <action></action>
    <expectedresults></expectedresults>
    <setup></setup>
    <breakdown></breakdown>
    <tag>xmlrpc</tag>
    <tag>haha</tag>
    <tag>case management system</tag>
  </testcase>
</testopia>
'''


xml_file_with_wrong_version = u'''
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<!DOCTYPE testopia SYSTEM "testopia.dtd" [
  <!ENTITY testopia_lt "<">
  <!ENTITY testopia_gt ">">
]>
<testopia version="who knows"></testopia>'''


xml_file_in_malformat = u'''
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<!DOCTYPE testopia SYSTEM "testopia.dtd" [
  <!ENTITY testopia_lt "<">
  <!ENTITY testopia_gt ">">
]>
<nitrate version="1.1"></nitrate>'''


class TestProcessCase(unittest.TestCase):
    '''Test process_case'''

    def setUp(self):
        self.xml2dict = XML2Dict()
        self.user = User.objects.create(username='xml user',
                                        email='user@example.com')
        result = Priority.objects.get_or_create(value='P1')
        self.priority_p1, self.priority_p1_created = result
        result = TestCaseStatus.objects.get_or_create(name='CONFIRMED')
        self.status_confirmed, self.status_confirmed_created = result
        result = TestCaseStatus.objects.get_or_create(name='PROPOSED')
        self.status_proposed, self.status_proposed_created = result

    def tearDown(self):
        self.user.delete()
        if self.priority_p1_created:
            self.priority_p1.delete()
        if self.status_confirmed_created:
            self.status_confirmed.delete()
        if self.status_proposed_created:
            self.status_proposed.delete()

    def _format_xml_case_string(self, case_data):
        '''Helper method to format case XML conveniently'''
        data = case_data.copy()
        data['tags'] = ''.join(
            '<tag>{0}</tag>'.format(tag) for tag in data['tag'])
        data.pop('tag')
        return xml_single_case % data

    def _create_xml_dict(self, case_data):
        xml_case = self._format_xml_case_string(case_data)
        return self.xml2dict.fromstring(xml_case)

    def test_process_case(self):
        xmldict = self._create_xml_dict(sample_case_data)

        cleaned_case = process_case(xmldict['testcase'])
        self.assertEqual(self.user.id, cleaned_case['author_id'])
        self.assertEqual(self.user, cleaned_case['author'])
        self.assertEqual(sample_case_data['summary'], cleaned_case['summary'])
        self.assertEqual(None, cleaned_case['default_tester_id'])
        p1 = Priority.objects.get(value=sample_case_data['priority'])
        self.assertEqual(p1.pk, cleaned_case['priority_id'])
        self.assertEqual(False, cleaned_case['is_automated'])
        self.assertEqual(sample_case_data['categoryname'],
                         cleaned_case['category_name'])
        self.assert_(isinstance(cleaned_case['tags'], list))
        for tag in sample_case_data['tag']:
            expected_tag = TestTag.objects.get(name=tag)
            self.assertEqual(expected_tag, cleaned_case['tags'][0])
        self.assertEqual(sample_case_data['action'], cleaned_case['action'])
        self.assertEqual(sample_case_data['effect'], cleaned_case['effect'])
        self.assertEqual(sample_case_data['setup'], cleaned_case['setup'])
        self.assertEqual(sample_case_data['breakdown'],
                         cleaned_case['breakdown'])
        self.assertEqual(sample_case_data['notes'], cleaned_case['notes'])

    def test_nonexistent_object(self):
        case_data = sample_case_data.copy()
        case_data['author'] = 'another_user@example.com'
        xmldict = self._create_xml_dict(case_data)
        self.assertRaises(User.DoesNotExist, process_case, xmldict['testcase'])

        case_data = sample_case_data.copy()
        case_data['defaulttester'] = 'another_user@example.com'
        xmldict = self._create_xml_dict(case_data)
        self.assertRaises(User.DoesNotExist, process_case, xmldict['testcase'])

        case_data = sample_case_data.copy()
        case_data['priority'] = 'PP'
        xmldict = self._create_xml_dict(case_data)
        self.assertRaises(Priority.DoesNotExist,
                          process_case, xmldict['testcase'])

        case_data = sample_case_data.copy()
        case_data['priority'] = ''
        xmldict = self._create_xml_dict(case_data)
        self.assertRaises(ValueError, process_case, xmldict['testcase'])

        case_data = sample_case_data.copy()
        case_data['status'] = 'UNKNOWN_STATUS'
        xmldict = self._create_xml_dict(case_data)
        self.assertRaises(TestCaseStatus.DoesNotExist,
                          process_case, xmldict['testcase'])

        case_data = sample_case_data.copy()
        case_data['status'] = ''
        xmldict = self._create_xml_dict(case_data)
        self.assertRaises(ValueError, process_case, xmldict['testcase'])

        case_data = sample_case_data.copy()
        case_data['automated'] = ''
        xmldict = self._create_xml_dict(case_data)
        cleaned_case = process_case(xmldict['testcase'])
        self.assertEqual(False, cleaned_case['is_automated'])

        case_data = sample_case_data.copy()
        case_data['tag'] = ''
        xmldict = self._create_xml_dict(case_data)
        cleaned_case = process_case(xmldict['testcase'])
        self.assertEqual(None, cleaned_case['tags'])

        case_data = sample_case_data.copy()
        case_data['categoryname'] = ''
        xmldict = self._create_xml_dict(case_data)
        self.assertRaises(ValueError, process_case, xmldict['testcase'])


class TestCleanXMLFile(unittest.TestCase):
    '''Test for testplan.clean_xml_file'''

    def setUp(self):
        self.user = User.objects.create(username='xml user',
                                        email='user@example.com')
        result = Priority.objects.get_or_create(value='P1')
        self.priority, self.priority_created = result
        result = TestCaseStatus.objects.get_or_create(name='CONFIRMED')
        self.status_confirmed, self.status_confirmed_created = result

        self.original_xml_version = None
        if hasattr(settings, 'TESTOPIA_XML_VERSION'):
            self.original_xml_version = settings.TESTOPIA_XML_VERSION
        settings.TESTOPIA_XML_VERSION = 1.1

    def tearDown(self):
        self.user.delete()
        if self.priority_created:
            self.priority.delete()
        if self.status_confirmed_created:
            self.status_confirmed.delete()
        if self.original_xml_version is not None:
            settings.TESTOPIA_XML_VERSION = self.original_xml_version

    def test_clean_xml_file(self):
        result = clean_xml_file(xml_file_without_error)
        self.assertEqual(2, len(result))

        result = clean_xml_file(xml_file_single_case_without_error)
        self.assertEqual(1, len(result))

        self.assertRaises(User.DoesNotExist,
                          clean_xml_file,
                          xml_file_with_error)

        self.assertRaises(ValueError, clean_xml_file, xml_file_in_malformat)

        self.assertRaises(ValueError,
                          clean_xml_file,
                          xml_file_with_wrong_version)


# ################ End of testing testplan.import_case_via_XML #############


class TestTestPlan(FastFixtureTestCase):
    '''Test serialization'''

    fixtures = ['unittest.json']

    test_fields = (
        'plan_id',
        'name',
        'create_date',
        'is_active',
        'extra_link',
        'default_product_version',

        # foreign keys
        'product_version', 'product_version_id',
        'owner', 'owner_id',
        'author', 'author_id',
        'product', 'product_id',
        'type', 'type_id',
        'parent', 'parent_id',

        # m2m fields
        'attachment',
        'case',
        'component',
        'env_group',
        'tag',
    )

    def setUp(self):
        self.plan_pks = [plan.pk for plan in TestPlan.objects.all()[:2]]

    def test_to_xmlrpc(self):
        result = TestPlan.to_xmlrpc(query={'pk__in': self.plan_pks})
        self.assertEqual(len(result), 2)

        # Verify fields
        sample_testplan = result[0]
        sample_fields = set(name for name in sample_testplan.keys())
        test_fields = set(self.test_fields)
        test_result = list(sample_fields ^ test_fields)
        self.assertEqual(test_result, [])

        result = dict([(item['plan_id'], item) for item in result])

        plan = result[self.plan_pks[0]]
        sample_plan = TestPlan.objects.get(pk=self.plan_pks[0])

        self.assertEqual(plan['name'], sample_plan.name)
        self.assertEqual(plan['is_active'], sample_plan.is_active)
        self.assertEqual(plan['product_version_id'],
                         sample_plan.product_version_id)

        components = plan['component']
        components.sort()
        sample_components = [item.pk for item in sample_plan.component.all()]
        sample_components.sort()
        self.assertEqual(components, sample_components)

        plan = result[self.plan_pks[1]]
        sample_plan = TestPlan.objects.get(pk=self.plan_pks[1])

        self.assertEqual(plan['name'], sample_plan.name)
        self.assertEqual(plan['is_active'], sample_plan.is_active)
        self.assertEqual(plan['product_version_id'],
                         sample_plan.product_version_id)
