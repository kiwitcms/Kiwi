# -*- coding: utf-8 -*-

import unittest

from httplib import BAD_REQUEST
from httplib import NOT_FOUND
from httplib import INTERNAL_SERVER_ERROR

from django import test
from django.conf import settings
from django.contrib.auth.models import User

from tcms.core.contrib.xml2dict.xml2dict import XML2Dict
from tcms.management.models import Priority
from tcms.management.models import TestTag
from tcms.testcases.models import TestCase
from tcms.testcases.models import TestCasePlan
from tcms.testcases.models import TestCaseStatus
from tcms.testplans.models import TestPlan
from tcms.testplans.models import TCMSEnvPlanMap
from tcms.xmlrpc.api import testplan as XmlrpcTestPlan
from tcms.xmlrpc.api.testplan import clean_xml_file
from tcms.xmlrpc.api.testplan import process_case
from tcms.xmlrpc.tests.utils import make_http_request
from tcms.xmlrpc.tests.utils import user_should_have_perm

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

__all__ = (
    'TestAddComponent',
    'TestAddTag',
    'TestCleanXMLFile',
    'TestComponentMethods',
    'TestFilter',
    'TestGetAllCasesTags',
    'TestGetProduct',
    'TestGetTestCases',
    'TestGetTestRuns',
    'TestGetText',
    'TestImportCaseViaXML',
    'TestPlanTypeMethods',
    'TestRemoveTag',
    'TestUpdate',
)


class TestFilter(XmlrpcAPIBaseTest):

    @classmethod
    def setUpClass(cls):
        super(TestFilter, cls).setUpClass()
        cls.product = ProductFactory()
        cls.version = VersionFactory(product=cls.product)
        cls.tester = UserFactory()
        cls.plan_type = TestPlanTypeFactory(name='manual smoking')
        cls.plan_1 = TestPlanFactory(product_version=cls.version,
                                     product=cls.product,
                                     author=cls.tester,
                                     type=cls.plan_type)
        cls.plan_2 = TestPlanFactory(product_version=cls.version,
                                     product=cls.product,
                                     author=cls.tester,
                                     type=cls.plan_type)
        cls.case_1 = TestCaseFactory(author=cls.tester,
                                     default_tester=None,
                                     reviewer=cls.tester,
                                     plan=[cls.plan_1])
        cls.case_2 = TestCaseFactory(author=cls.tester,
                                     default_tester=None,
                                     reviewer=cls.tester,
                                     plan=[cls.plan_1])

    @classmethod
    def tearDownClass(cls):
        cls.plan_1.case.clear()
        cls.plan_2.case.clear()
        cls.case_1.delete()
        cls.case_2.delete()
        cls.plan_1.delete()
        cls.plan_2.delete()
        cls.plan_type.delete()
        cls.tester.delete()
        cls.version.delete()
        cls.product.delete()
        cls.product.classification.delete()

    def test_filter_plans(self):
        plans = XmlrpcTestPlan.filter(None, {'pk__in': [self.plan_1.pk, self.plan_2.pk]})
        plan = plans[0]
        self.assertEqual(self.plan_1.name, plan['name'])
        self.assertEqual(self.plan_1.product_version.pk, plan['product_version_id'])
        self.assertEqual(self.plan_1.author.pk, plan['author_id'])

        self.assertEqual(2, len(plan['case']))
        self.assertEqual([self.case_1.pk, self.case_2.pk], plan['case'])
        self.assertEqual(0, len(plans[1]['case']))

    def test_filter_out_all_plans(self):
        plans_total = TestPlan.objects.all().count()
        self.assertEqual(plans_total, len(XmlrpcTestPlan.filter(None)))
        self.assertEqual(plans_total, len(XmlrpcTestPlan.filter(None, {})))


class TestAddTag(XmlrpcAPIBaseTest):

    @classmethod
    def setUpClass(cls):
        cls.user = UserFactory()
        cls.http_req = make_http_request(user=cls.user)
        user_should_have_perm(cls.http_req.user, 'testplans.add_testplantag')

        cls.product = ProductFactory()
        cls.plans = [
            TestPlanFactory(author=cls.user, owner=cls.user, product=cls.product),
            TestPlanFactory(author=cls.user, owner=cls.user, product=cls.product),
        ]

        cls.tag1 = TestTagFactory(name='xmlrpc_test_tag_1')
        cls.tag2 = TestTagFactory(name='xmlrpc_test_tag_2')
        cls.tag_name = 'xmlrpc_tag_name_1'

    @classmethod
    def tearDownClass(cls):
        for plan in cls.plans:
            plan.tag.clear()
            plan.delete()
        cls.product.delete()
        cls.product.classification.delete()
        cls.tag1.delete()
        cls.tag2.delete()
        cls.user.delete()

    def test_single_id(self):
        '''Test with singal plan id and tag id'''
        self.assertRaisesXmlrpcFault(INTERNAL_SERVER_ERROR, XmlrpcTestPlan.add_tag,
                                     self.http_req, self.plans[0].pk, self.tag1.pk)

        XmlrpcTestPlan.add_tag(self.http_req, self.plans[0].pk, self.tag1.name)
        tag_exists = TestPlan.objects.filter(pk=self.plans[0].pk, tag__pk=self.tag1.pk).exists()
        self.assert_(tag_exists)

    def test_array_argument(self):
        XmlrpcTestPlan.add_tag(self.http_req, self.plans[0].pk, [self.tag2.name, self.tag_name])
        tag_exists = TestPlan.objects.filter(pk=self.plans[0].pk,
                                             tag__name__in=[self.tag2.name, self.tag_name])
        self.assert_(tag_exists.exists())

        plans_ids = [plan.pk for plan in self.plans]
        tags_names = [self.tag_name, 'xmlrpc_tag_name_2']
        XmlrpcTestPlan.add_tag(self.http_req, plans_ids, tags_names)
        for plan in self.plans:
            tag_exists = plan.tag.filter(name__in=tags_names).exists()
            self.assert_(tag_exists)


class TestAddComponent(XmlrpcAPIBaseTest):

    @classmethod
    def setUpClass(cls):
        cls.user = UserFactory()
        cls.http_req = make_http_request(user=cls.user)
        perm_name = 'testplans.add_testplancomponent'
        user_should_have_perm(cls.http_req.user, perm_name)

        cls.product = ProductFactory()
        cls.plans = [
            TestPlanFactory(author=cls.user, owner=cls.user, product=cls.product),
            TestPlanFactory(author=cls.user, owner=cls.user, product=cls.product),
        ]
        cls.component1 = ComponentFactory(name='xmlrpc test component 1',
                                          description='xmlrpc test description',
                                          product=cls.product,
                                          initial_owner=None,
                                          initial_qa_contact=None)
        cls.component2 = ComponentFactory(name='xmlrpc test component 2',
                                          description='xmlrpc test description',
                                          product=cls.product,
                                          initial_owner=None,
                                          initial_qa_contact=None)

    @classmethod
    def tearDownClass(cls):
        cls.component1.delete()
        cls.component2.delete()
        for plan in cls.plans:
            plan.component.clear()
            plan.delete()
        cls.product.delete()
        cls.product.classification.delete()
        cls.user.delete()

    def test_single_id(self):
        XmlrpcTestPlan.add_component(self.http_req, self.plans[0].pk, self.component1.pk)
        component_exists = TestPlan.objects.filter(
            pk=self.plans[0].pk, component__pk=self.component1.pk).exists()
        self.assertTrue(component_exists)

    def test_ids_in_array(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, XmlrpcTestPlan.add_component,
                                     self.http_req, [1, 2])

        plans_ids = [plan.pk for plan in self.plans]
        components_ids = [self.component1.pk, self.component2.pk]
        XmlrpcTestPlan.add_component(self.http_req, plans_ids, components_ids)
        for plan in TestPlan.objects.filter(pk__in=plans_ids):
            components_ids = [item.pk for item in plan.component.iterator()]
            self.assertTrue(self.component1.pk in components_ids)
            self.assertTrue(self.component2.pk in components_ids)


class TestPlanTypeMethods(XmlrpcAPIBaseTest):

    @classmethod
    def setUpClass(cls):
        cls.http_req = make_http_request()
        cls.plan_type = TestPlanTypeFactory(name='xmlrpc plan type', description='')

    @classmethod
    def tearDownClass(cls):
        cls.plan_type.delete()

    def test_check_plan_type(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, XmlrpcTestPlan.check_plan_type, self.http_req)

        result = XmlrpcTestPlan.check_plan_type(self.http_req, self.plan_type.name)
        self.assertEqual(self.plan_type.name, result['name'])
        self.assertEqual(self.plan_type.description, result['description'])
        self.assertEqual(self.plan_type.pk, result['id'])

    def test_get_plan_type(self):
        result = XmlrpcTestPlan.get_plan_type(self.http_req, self.plan_type.pk)
        self.assertEqual(self.plan_type.name, result['name'])
        self.assertEqual(self.plan_type.description, result['description'])
        self.assertEqual(self.plan_type.pk, result['id'])

        self.assertRaisesXmlrpcFault(NOT_FOUND, XmlrpcTestPlan.get_plan_type, self.http_req, 0)
        self.assertRaisesXmlrpcFault(NOT_FOUND, XmlrpcTestPlan.get_plan_type, self.http_req, -2)


class TestGetProduct(XmlrpcAPIBaseTest):

    @classmethod
    def setUpClass(cls):
        cls.http_req = make_http_request()
        cls.user = UserFactory()
        cls.product = ProductFactory()
        cls.plan = TestPlanFactory(author=cls.user, owner=cls.user, product=cls.product)

    @classmethod
    def tearDownClass(cls):
        cls.plan.delete()
        cls.product.delete()
        cls.product.classification.delete()
        cls.user.delete()

    def _verify_serialize_result(self, result):
        self.assertEqual(self.plan.product.name, result['name'])
        self.assertEqual(self.plan.product.description, result['description'])
        self.assertEqual(self.plan.product.disallow_new, result['disallow_new'])
        self.assertEqual(self.plan.product.vote_super_user, result['vote_super_user'])
        self.assertEqual(self.plan.product.max_vote_super_bug, result['max_vote_super_bug'])
        self.assertEqual(self.plan.product.votes_to_confirm, result['votes_to_confirm'])
        self.assertEqual(self.plan.product.default_milestone, result['default_milestone'])
        self.assertEqual(self.plan.product.classification.pk, result['classification_id'])
        self.assertEqual(self.plan.product.classification.name, result['classification'])

    def test_get_product(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, XmlrpcTestPlan.get_product, self.http_req, 0)

        result = XmlrpcTestPlan.get_product(self.http_req, str(self.plan.pk))
        self._verify_serialize_result(result)

        result = XmlrpcTestPlan.get_product(self.http_req, self.plan.pk)
        self._verify_serialize_result(result)

        self.assertRaisesXmlrpcFault(BAD_REQUEST, XmlrpcTestPlan.get_product,
                                     self.http_req, 'plan_id')


@unittest.skip('TODO: test case is not implemented yet.')
class TestComponentMethods(test.TestCase):
    '''TODO: '''


@unittest.skip('TODO: test case is not implemented yet.')
class TestGetAllCasesTags(test.TestCase):
    '''TODO: '''


class TestGetTestCases(XmlrpcAPIBaseTest):
    '''Test testplan.get_test_cases method'''

    @classmethod
    def setUpClass(cls):
        cls.http_req = make_http_request()

        cls.tester = UserFactory(username='tester')
        cls.reviewer = UserFactory(username='reviewer')
        cls.product = ProductFactory()
        cls.plan = TestPlanFactory(author=cls.tester, owner=cls.tester, product=cls.product)
        cls.cases = [
            TestCaseFactory(author=cls.tester, default_tester=None, reviewer=cls.reviewer,
                            plan=[cls.plan]),
            TestCaseFactory(author=cls.tester, default_tester=None, reviewer=cls.reviewer,
                            plan=[cls.plan]),
            TestCaseFactory(author=cls.tester, default_tester=None, reviewer=cls.reviewer,
                            plan=[cls.plan]),
        ]
        cls.another_plan = TestPlanFactory(author=cls.tester, owner=cls.tester, product=cls.product)

    @classmethod
    def tearDownClass(cls):
        for case in cls.cases:
            case.plan.clear()
            case.delete()
        cls.plan.delete()
        cls.product.delete()
        cls.product.classification.delete()
        cls.reviewer.delete()
        cls.tester.delete()

    def test_get_test_cases(self):
        serialized_cases = XmlrpcTestPlan.get_test_cases(self.http_req, self.plan.pk)
        for case in serialized_cases:
            expected_case = TestCase.objects.filter(plan=self.plan.pk).get(pk=case['case_id'])

            self.assertEqual(expected_case.summary, case['summary'])
            self.assertEqual(expected_case.priority_id, case['priority_id'])
            self.assertEqual(expected_case.author_id, case['author_id'])

            plan_case_rel = TestCasePlan.objects.get(plan=self.plan, case=case['case_id'])
            self.assertEqual(plan_case_rel.sortkey, case['sortkey'])

    @unittest.skip('TODO: fix get_test_cases to make this test pass.')
    def test_different_argument_type(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, XmlrpcTestPlan.get_test_cases,
                                     self.http_req, str(self.plan.pk))

    def test_404_when_plan_nonexistent(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, XmlrpcTestPlan.get_test_cases, self.http_req, 0)

        plan_id = TestPlan.objects.order_by('-pk')[:1][0].pk + 1
        self.assertRaisesXmlrpcFault(NOT_FOUND, XmlrpcTestPlan.get_test_cases,
                                     self.http_req, plan_id)

    def test_plan_has_no_cases(self):
        result = XmlrpcTestPlan.get_test_cases(self.http_req, self.another_plan.pk)
        self.assertEqual([], result)


@unittest.skip('TODO: test case is not implemented yet.')
class TestGetTestRuns(test.TestCase):
    '''TODO: '''


@unittest.skip('TODO: test case is not implemented yet.')
class TestGetText(test.TestCase):
    '''TODO: '''


@unittest.skip('TODO: test case is not implemented yet.')
class TestRemoveTag(test.TestCase):
    '''TODO: '''


@unittest.skip('TODO: test case is not implemented yet.')
class TestImportCaseViaXML(test.TestCase):
    '''TODO: '''


class TestUpdate(test.TestCase):
    ''' Tests the XMLRPM testplan.update method '''
    @classmethod
    def setUpClass(cls):
        super(TestUpdate, cls).setUpClass()

        cls.user = UserFactory()
        cls.http_req = make_http_request(user=cls.user)
        perm_name = 'testplans.change_testplan'
        user_should_have_perm(cls.http_req.user, perm_name)

        cls.env_group_1 = TCMSEnvGroupFactory()
        cls.env_group_2 = TCMSEnvGroupFactory()
        cls.product = ProductFactory()
        cls.version = VersionFactory(product=cls.product)
        cls.tester = UserFactory()
        cls.plan_type = TestPlanTypeFactory(name='manual smoking')
        cls.plan_1 = TestPlanFactory(product_version=cls.version,
                                     product=cls.product,
                                     author=cls.tester,
                                     type=cls.plan_type,
                                     env_group=(cls.env_group_1,))
        cls.plan_2 = TestPlanFactory(product_version=cls.version,
                                     product=cls.product,
                                     author=cls.tester,
                                     type=cls.plan_type,
                                     env_group=(cls.env_group_1,))

    @classmethod
    def tearDownClass(cls):
        cls.plan_1.delete()
        cls.plan_2.delete()
        cls.plan_type.delete()
        cls.tester.delete()
        cls.user.delete()
        cls.version.delete()
        cls.product.delete()
        cls.product.classification.delete()
        cls.env_group_1.delete()
        cls.env_group_2.delete()

    def test_update_env_group(self):
        # first verify that plan_1 and plan_2 point to self.env_group_1
        self.assertEqual(self.plan_1.env_group.count(), 1)
        self.assertEqual(self.plan_1.env_group.all()[0].pk, self.env_group_1.pk)

        self.assertEqual(self.plan_2.env_group.count(), 1)
        self.assertEqual(self.plan_2.env_group.all()[0].pk, self.env_group_1.pk)

        # and there are only 2 objects in the many-to-many table
        self.assertEqual(TCMSEnvPlanMap.objects.count(), 2)

        # then issue XMLRPC request to modify the env_group of self.plan_2
        plans = XmlrpcTestPlan.update(self.http_req, self.plan_2.pk, {'env_group': self.env_group_2.pk})
        plan = plans[0]

        # now verify that the returned TP (plan_2) has been updated to env_group_2
        self.assertEqual(plan['plan_id'], self.plan_2.pk)
        self.assertEqual(len(plan['env_group']), 1)
        self.assertEqual(plan['env_group'][0], self.env_group_2.pk)

        # and that plan_1 has not changed at all
        self.assertEqual(self.plan_1.env_group.count(), 1)
        self.assertEqual(self.plan_1.env_group.all()[0].pk, self.env_group_1.pk)

        # and there are still only 2 objects in the many-to-many table
        # iow no dangling objects left
        self.assertEqual(TCMSEnvPlanMap.objects.count(), 2)


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


class TestProcessCase(test.TestCase):
    '''Test process_case'''

    @classmethod
    def setUpClass(cls):
        cls.xml2dict = XML2Dict()
        cls.user = UserFactory(username='xml user', email='user@example.com')
        cls.priority_p1, created = Priority.objects.get_or_create(value='P1')
        cls.status_confirmed, created = TestCaseStatus.objects.get_or_create(name='CONFIRMED')
        cls.status_proposed, created = TestCaseStatus.objects.get_or_create(name='PROPOSED')

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()

    def _format_xml_case_string(self, case_data):
        """Helper method to format case XML conveniently"""
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


class TestCleanXMLFile(test.TestCase):
    '''Test for testplan.clean_xml_file'''

    @classmethod
    def setUpClass(cls):
        cls.user = UserFactory(username='xml user', email='user@example.com')
        cls.priority = Priority.objects.get(value='P1')
        cls.status_confirmed = TestCaseStatus.objects.get(name='CONFIRMED')

        cls.original_xml_version = None
        if hasattr(settings, 'TESTOPIA_XML_VERSION'):
            cls.original_xml_version = settings.TESTOPIA_XML_VERSION
        settings.TESTOPIA_XML_VERSION = 1.1

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
        if cls.original_xml_version is not None:
            settings.TESTOPIA_XML_VERSION = cls.original_xml_version

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
