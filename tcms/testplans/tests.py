# -*- coding: utf-8 -*-

import json
import httplib
import os
import xml.etree.ElementTree as et

from six.moves import http_client
from six.moves import map

from django import test
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client

from tcms.core.logs.models import TCMSLogModel
from tcms.settings.common import TCMS_ROOT_PATH
from tcms.testcases.models import TestCase
from tcms.testcases.models import TestCasePlan
from tcms.testplans.models import TestPlan
from tcms.tests import BasePlanCase
from tcms.tests import remove_perm_from_user
from tcms.tests import user_should_have_perm
from tcms.tests.factories import ClassificationFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestPlanTypeFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory


class PlanTests(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(username='admin', email='admin@example.com')
        cls.user.set_password('admin')
        cls.user.is_superuser = True
        cls.user.save()

        cls.c = Client()
        cls.c.login(username='admin', password='admin')

        cls.classification = ClassificationFactory(name='Auto')
        cls.product = ProductFactory(name='Nitrate', classification=cls.classification)
        cls.product_version = VersionFactory(value='0.1', product=cls.product)
        cls.plan_type = TestPlanTypeFactory()

        cls.test_plan = TestPlanFactory(name='another test plan for testing',
                                        product_version=cls.product_version,
                                        owner=cls.user,
                                        author=cls.user,
                                        product=cls.product,
                                        type=cls.plan_type)
        cls.plan_id = cls.test_plan.pk

    def test_open_plans_search(self):
        location = reverse('tcms.testplans.views.all')
        response = self.c.get(location)
        self.assertEquals(response.status_code, httplib.OK)

    def test_search_plans(self):
        location = reverse('tcms.testplans.views.all')
        response = self.c.get(location, {'action': 'search', 'type': self.test_plan.type.pk})
        self.assertEquals(response.status_code, httplib.OK)

    def test_plan_new_get(self):
        location = reverse('tcms.testplans.views.new')
        response = self.c.get(location, follow=True)
        self.assertEquals(response.status_code, httplib.OK)

    def test_plan_clone(self):
        location = reverse('tcms.testplans.views.clone')
        response = self.c.get(location, {'plan_id': self.plan_id})
        self.assertEquals(response.status_code, httplib.OK)

    def test_plan_details(self):
        location = reverse('tcms.testplans.views.get', args=[self.plan_id])
        response = self.c.get(location)
        self.assertEquals(response.status_code, httplib.MOVED_PERMANENTLY)

        response = self.c.get(location, follow=True)
        self.assertEquals(response.status_code, httplib.OK)

    def test_plan_cases(self):
        location = reverse('tcms.testplans.views.cases', args=[self.plan_id])
        response = self.c.get(location)
        self.assertEquals(response.status_code, httplib.OK)

    def test_plan_importcase(self):
        location = reverse('tcms.testplans.views.cases', args=[self.plan_id])
        filename = os.path.join(TCMS_ROOT_PATH, 'fixtures', 'cases-to-import.xml')
        with open(filename, 'r') as fin:
            response = self.c.post(location, {'a': 'import_cases', 'xml_file': fin}, follow=True)
        self.assertEquals(response.status_code, httplib.OK)

        summary = 'Remove this case from a test plan'
        has_case = TestCase.objects.filter(summary=summary).exists()
        self.assertTrue(has_case)

    def test_plan_delete(self):
        tp_pk = self.test_plan.pk

        location = reverse('tcms.testplans.views.delete', args=[tp_pk])
        response = self.c.get(location)
        self.assertEquals(response.status_code, httplib.OK)

        response = self.c.get(location, {'sure': 'no'})
        self.assertEquals(response.status_code, httplib.OK)

        response = self.c.get(location, {'sure': 'yes'})
        self.assertEquals(response.status_code, httplib.OK)
        deleted = not TestPlan.objects.filter(pk=tp_pk).exists()
        self.assert_(deleted,
                     'TestPlan {0} should be deleted. But, not.'.format(tp_pk))

    def test_plan_edit(self):
        location = reverse('tcms.testplans.views.edit', args=[self.plan_id])
        response = self.c.get(location)
        self.assertEquals(response.status_code, httplib.OK)

    def test_plan_printable(self):
        location = reverse('tcms.testplans.views.printable')
        response = self.c.get(location, {'plan_id': self.plan_id})
        self.assertEquals(response.status_code, httplib.OK)

    def test_plan_export(self):
        location = reverse('tcms.testplans.views.export')
        response = self.c.get(location, {'plan': self.plan_id})
        self.assertEquals(response.status_code, httplib.OK)

        xml_doc = response.content
        try:
            et.fromstring(xml_doc)
        except et.ParseError:
            self.fail('XML document exported from test plan is invalid.')

    def test_plan_attachment(self):
        location = reverse('tcms.testplans.views.attachment',
                           args=[self.plan_id])
        response = self.c.get(location)
        self.assertEquals(response.status_code, httplib.OK)

    def test_plan_history(self):
        location = reverse('tcms.testplans.views.text_history',
                           args=[self.plan_id])
        response = self.c.get(location)
        self.assertEquals(response.status_code, httplib.OK)

        response = self.c.get(location, {'plan_text_version': 1})
        self.assertEquals(response.status_code, httplib.OK)


class TestPlanModel(test.TestCase):
    """ Test some model operations directly without a view """

    @classmethod
    def setUpTestData(cls):
        cls.plan_1 = TestPlanFactory()
        cls.testcase_1 = TestCaseFactory()
        cls.testcase_2 = TestCaseFactory()

        cls.plan_1.add_case(cls.testcase_1)
        cls.plan_1.add_case(cls.testcase_2)

    def test_plan_delete(self):
        self.plan_1.delete_case(self.testcase_1)
        cases_left = TestCasePlan.objects.filter(plan=self.plan_1.pk)
        self.assertEqual(1, cases_left.count())
        self.assertEqual(self.testcase_2.pk, cases_left[0].case.pk)


# ### Test cases for view methods ### #


class TestUnknownActionOnCases(BasePlanCase):
    """Test case for unknown action on a plan's cases"""

    def setUp(self):
        self.cases_url = reverse('tcms.testplans.views.cases', args=[self.plan.pk])
        self.client = Client()

    def test_ajax_request(self):
        response = self.client.get(self.cases_url, {'a': 'unknown action', 'format': 'json'})
        data = json.loads(response.content)
        self.assertEqual('Unrecognizable actions', data['response'])

    def test_request_from_webui(self):
        response = self.client.get(self.cases_url, {'a': 'unknown action'})
        self.assertContains(response, 'Unrecognizable actions')


class TestDeleteCasesFromPlan(BasePlanCase):
    """Test case for deleting cases from a plan"""

    @classmethod
    def setUpTestData(cls):
        super(TestDeleteCasesFromPlan, cls).setUpTestData()
        cls.plan_tester = User(username='tester')
        cls.plan_tester.set_password('password')
        cls.plan_tester.save()

    def setUp(self):
        self.cases_url = reverse('tcms.testplans.views.cases', args=[self.plan.pk])
        self.client = Client()
        self.client.login(username=self.plan_tester.username, password='password')

    def tearDown(self):
        self.client.logout()

    def test_missing_cases_ids(self):
        response = self.client.post(self.cases_url, {'a': 'delete_cases'})
        data = json.loads(response.content)
        self.assertEqual(1, data['rc'])
        self.assertEqual('At least one case is required to delete.', data['response'])

    def test_delete_cases(self):
        post_data = {'a': 'delete_cases', 'case': [self.case_1.pk, self.case_3.pk]}
        response = self.client.post(self.cases_url, post_data)
        data = json.loads(response.content)

        self.assertEqual(0, data['rc'])
        self.assertEqual('ok', data['response'])
        self.assertFalse(self.plan.case.filter(pk__in=[self.case_1.pk, self.case_3.pk]).exists())

        # Assert action logs are recorded for plan and case correctly

        expected_log = 'Remove from plan {}'.format(self.plan.pk)
        for pk in (self.case_1.pk, self.case_3.pk):
            log = TCMSLogModel.get_logs_for_model(TestCase, pk)[0]
            self.assertEqual(expected_log, log.action)

        for plan_pk, case_pk in ((self.plan.pk, self.case_1.pk), (self.plan.pk, self.case_3.pk)):
            expected_log = 'Remove case {} from plan {}'.format(case_pk, plan_pk)
            self.assertTrue(TCMSLogModel.objects.filter(action=expected_log).exists())


class TestSortCases(BasePlanCase):
    """Test case for sorting cases"""

    @classmethod
    def setUpTestData(cls):
        super(TestSortCases, cls).setUpTestData()
        cls.plan_tester = User(username='tester')
        cls.plan_tester.set_password('password')
        cls.plan_tester.save()

    def setUp(self):
        self.cases_url = reverse('tcms.testplans.views.cases', args=[self.plan.pk])
        self.client = Client()
        self.client.login(username=self.plan_tester.username, password='password')

    def tearDown(self):
        self.client.logout()

    def test_missing_cases_ids(self):
        response = self.client.post(self.cases_url, {'a': 'order_cases'})
        data = json.loads(response.content)
        self.assertEqual(1, data['rc'])
        self.assertEqual('At least one case is required to re-order.', data['response'])

    def test_order_cases(self):
        post_data = {'a': 'order_cases', 'case': [self.case_1.pk, self.case_3.pk]}
        response = self.client.post(self.cases_url, post_data)
        data = json.loads(response.content)

        self.assertEqual(0, data['rc'])
        self.assertEqual('ok', data['response'])

        case_plan_rel = TestCasePlan.objects.get(plan=self.plan, case=self.case_1)
        self.assertEqual(10, case_plan_rel.sortkey)

        case_plan_rel = TestCasePlan.objects.get(plan=self.plan, case=self.case_3)
        self.assertEqual(20, case_plan_rel.sortkey)


class TestLinkCases(BasePlanCase):
    """Test case for linking cases from other plans"""

    @classmethod
    def setUpTestData(cls):
        super(TestLinkCases, cls).setUpTestData()

        cls.another_plan = TestPlanFactory(author=cls.tester, owner=cls.tester,
                                           product=cls.product, product_version=cls.version)
        cls.another_case_1 = TestCaseFactory(author=cls.tester, default_tester=None, reviewer=cls.tester,
                                             plan=[cls.another_plan])
        cls.another_case_2 = TestCaseFactory(author=cls.tester, default_tester=None, reviewer=cls.tester,
                                             plan=[cls.another_plan])

        cls.plan_tester = User(username='tester')
        cls.plan_tester.set_password('password')
        cls.plan_tester.save()

    def setUp(self):
        self.cases_url = reverse('tcms.testplans.views.cases', args=[self.plan.pk])
        self.client = Client()
        self.client.login(username=self.plan_tester.username, password='password')

    def tearDown(self):
        self.client.logout()

        # Ensure permission is removed whenever it was added during tests
        remove_perm_from_user(self.plan_tester, 'testcases.add_testcaseplan')

    def assert_quick_search_is_shown(self, response):
        self.assertContains(
            response,
            '<li class="profile_tab_active" id="quick_tab">')

    def assert_normal_search_is_shown(self, response):
        self.assertContains(
            response,
            '<li class="profile_tab_active" id="normal_tab">')

    def test_show_quick_search_by_default(self):
        response = self.client.post(self.cases_url, {'a': 'link_cases'})
        self.assert_quick_search_is_shown(response)

    def assert_search_result(self, response):
        self.assertContains(
            response,
            '<a href="{}">{}</a>'.format(
                reverse('tcms.testcases.views.get', args=[self.another_case_2.pk]),
                self.another_case_2.pk))

        # Assert: Do not list case that already belongs to the plan
        self.assertNotContains(
            response,
            '<a href="{}">{}</a>'.format(
                reverse('tcms.testcases.views.get', args=[self.case_2.pk]),
                self.case_2.pk))

    def test_quick_search(self):
        post_data = {'a': 'link_cases', 'action': 'search', 'search_mode': 'quick',
                     'case_id_set': ','.join(map(str, [self.case_1.pk, self.another_case_2.pk]))}
        response = self.client.post(self.cases_url, post_data)

        self.assert_quick_search_is_shown(response)
        self.assert_search_result(response)

    def test_normal_search(self):
        post_data = {'a': 'link_cases', 'action': 'search', 'search_mode': 'normal',
                     'case_id_set': ','.join(map(str, [self.case_1.pk, self.another_case_2.pk]))}
        response = self.client.post(self.cases_url, post_data)

        self.assert_normal_search_is_shown(response)
        self.assert_search_result(response)

    def test_missing_permission_to_link_cases(self):
        post_data = {'a': 'link_cases', 'action': 'add_to_plan',
                     'case': [self.another_case_1.pk, self.another_case_2.pk]}
        response = self.client.post(self.cases_url, post_data)
        self.assertContains(response, 'Permission Denied')

    def test_link_cases(self):
        user_should_have_perm(self.plan_tester, 'testcases.add_testcaseplan')

        post_data = {'a': 'link_cases', 'action': 'add_to_plan',
                     'case': [self.another_case_1.pk, self.another_case_2.pk]}
        response = self.client.post(self.cases_url, post_data)

        self.assertRedirects(
            response,
            reverse('tcms.testplans.views.get', args=[self.plan.pk]),
            target_status_code=http_client.MOVED_PERMANENTLY)

        self.assertTrue(
            TestCasePlan.objects.filter(plan=self.plan, case=self.another_case_1).exists())
        self.assertTrue(
            TestCasePlan.objects.filter(plan=self.plan, case=self.another_case_2).exists())
