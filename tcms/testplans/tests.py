# -*- coding: utf-8 -*-

from __future__ import division

import os
import xml.etree.ElementTree as et

from six.moves import http_client
from six.moves import map
from six.moves import urllib
from six.moves import zip

from django import test
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client

from tcms.core.logs.models import TCMSLogModel
from tcms.management.models import Product
from tcms.management.models import Version
from tcms.settings.common import TCMS_ROOT_PATH
from tcms.testcases.models import TestCase
from tcms.testcases.models import TestCasePlan
from tcms.testplans.models import TCMSEnvPlanMap
from tcms.testplans.models import TestPlan
from tcms.testplans.models import TestPlanAttachment
from tcms.tests.factories import ClassificationFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestPlanTypeFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory
from tcms.tests import BasePlanCase
from tcms.tests import remove_perm_from_user
from tcms.tests import user_should_have_perm
from tcms.tests import json_loads


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
        location = reverse('plans-all')
        response = self.c.get(location)
        self.assertEquals(response.status_code, http_client.OK)

    def test_search_plans(self):
        location = reverse('plans-all')
        response = self.c.get(location, {'action': 'search', 'type': self.test_plan.type.pk})
        self.assertEquals(response.status_code, http_client.OK)

    def test_plan_new_get(self):
        location = reverse('plans-new')
        response = self.c.get(location, follow=True)
        self.assertEquals(response.status_code, http_client.OK)

    def test_plan_details(self):
        location = reverse('plan-get', args=[self.plan_id])
        response = self.c.get(location)
        self.assertEquals(response.status_code, http_client.MOVED_PERMANENTLY)

        response = self.c.get(location, follow=True)
        self.assertEquals(response.status_code, http_client.OK)

    def test_plan_cases(self):
        location = reverse('plan-cases', args=[self.plan_id])
        response = self.c.get(location)
        self.assertEquals(response.status_code, http_client.OK)

    def test_plan_importcase(self):
        location = reverse('plan-cases', args=[self.plan_id])
        filename = os.path.join(TCMS_ROOT_PATH, 'fixtures', 'cases-to-import.xml')
        with open(filename, 'r') as fin:
            response = self.c.post(location, {'a': 'import_cases', 'xml_file': fin}, follow=True)
        self.assertEquals(response.status_code, http_client.OK)

        summary = 'Remove this case from a test plan'
        has_case = TestCase.objects.filter(summary=summary).exists()
        self.assertTrue(has_case)

    def test_plan_delete(self):
        tp_pk = self.test_plan.pk

        location = reverse('plan-delete', args=[tp_pk])
        response = self.c.get(location)
        self.assertEquals(response.status_code, http_client.OK)

        response = self.c.get(location, {'sure': 'no'})
        self.assertEquals(response.status_code, http_client.OK)

        response = self.c.get(location, {'sure': 'yes'})
        self.assertEquals(response.status_code, http_client.OK)
        deleted = not TestPlan.objects.filter(pk=tp_pk).exists()
        self.assert_(deleted,
                     'TestPlan {0} should be deleted. But, not.'.format(tp_pk))

    def test_plan_edit(self):
        location = reverse('plan-edit', args=[self.plan_id])
        response = self.c.get(location)
        self.assertEquals(response.status_code, http_client.OK)

    def test_plan_printable(self):
        location = reverse('plans-printable')
        response = self.c.get(location, {'plan_id': self.plan_id})
        self.assertEquals(response.status_code, http_client.OK)

    def test_plan_export(self):
        location = reverse('plans-export')
        response = self.c.get(location, {'plan': self.plan_id})
        self.assertEquals(response.status_code, http_client.OK)

        xml_doc = response.content
        try:
            et.fromstring(xml_doc)
        except et.ParseError:
            self.fail('XML document exported from test plan is invalid.')

    def test_plan_attachment(self):
        location = reverse('plan-attachment', args=[self.plan_id])
        response = self.c.get(location)
        self.assertEquals(response.status_code, http_client.OK)

    def test_plan_history(self):
        location = reverse('plan-text-history',
                           args=[self.plan_id])
        response = self.c.get(location)
        self.assertEquals(response.status_code, http_client.OK)

        response = self.c.get(location, {'plan_text_version': 1})
        self.assertEquals(response.status_code, http_client.OK)


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
        self.cases_url = reverse('plan-cases', args=[self.plan.pk])

    def test_ajax_request(self):
        response = self.client.get(self.cases_url, {'a': 'unknown action', 'format': 'json'})
        data = json_loads(response.content)
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

        cls.cases_url = reverse('plan-cases', args=[cls.plan.pk])

    def test_missing_cases_ids(self):
        self.client.login(username=self.plan_tester.username, password='password')

        response = self.client.post(self.cases_url, {'a': 'delete_cases'})
        data = json_loads(response.content)
        self.assertEqual(1, data['rc'])
        self.assertEqual('At least one case is required to delete.', data['response'])

    def test_delete_cases(self):
        self.client.login(username=self.plan_tester.username, password='password')

        post_data = {'a': 'delete_cases', 'case': [self.case_1.pk, self.case_3.pk]}
        response = self.client.post(self.cases_url, post_data)
        data = json_loads(response.content)

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

        cls.cases_url = reverse('plan-cases', args=[cls.plan.pk])

    def test_missing_cases_ids(self):
        self.client.login(username=self.plan_tester.username, password='password')

        response = self.client.post(self.cases_url, {'a': 'order_cases'})
        data = json_loads(response.content)
        self.assertEqual(1, data['rc'])
        self.assertEqual('At least one case is required to re-order.', data['response'])

    def test_order_cases(self):
        self.client.login(username=self.plan_tester.username, password='password')

        post_data = {'a': 'order_cases', 'case': [self.case_1.pk, self.case_3.pk]}
        response = self.client.post(self.cases_url, post_data)
        data = json_loads(response.content)

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

        cls.another_plan = TestPlanFactory(
            author=cls.tester,
            owner=cls.tester,
            product=cls.product,
            product_version=cls.version)

        cls.another_case_1 = TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            plan=[cls.another_plan])

        cls.another_case_2 = TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            plan=[cls.another_plan])

        cls.plan_tester = User(username='tester')
        cls.plan_tester.set_password('password')
        cls.plan_tester.save()

        cls.cases_url = reverse('plan-cases', args=[cls.plan.pk])

    def tearDown(self):
        # Ensure permission is removed whenever it was added during tests
        remove_perm_from_user(self.plan_tester, 'testcases.add_testcaseplan')

    def assert_quick_search_is_shown(self, response):
        self.client.login(username=self.plan_tester.username, password='password')

        self.assertContains(
            response,
            '<li class="profile_tab_active" id="quick_tab">')

    def assert_normal_search_is_shown(self, response):
        self.client.login(username=self.plan_tester.username, password='password')

        self.assertContains(
            response,
            '<li class="profile_tab_active" id="normal_tab">')

    def test_show_quick_search_by_default(self):
        self.client.login(username=self.plan_tester.username, password='password')

        response = self.client.post(self.cases_url, {'a': 'link_cases'})
        self.assert_quick_search_is_shown(response)

    def assert_search_result(self, response):
        self.client.login(username=self.plan_tester.username, password='password')

        self.assertContains(
            response,
            '<a href="{}">{}</a>'.format(
                reverse('case-get', args=[self.another_case_2.pk]),
                self.another_case_2.pk))

        # Assert: Do not list case that already belongs to the plan
        self.assertNotContains(
            response,
            '<a href="{}">{}</a>'.format(
                reverse('case-get', args=[self.case_2.pk]),
                self.case_2.pk))

    def test_quick_search(self):
        self.client.login(username=self.plan_tester.username, password='password')

        post_data = {'a': 'link_cases', 'action': 'search', 'search_mode': 'quick',
                     'case_id_set': ','.join(map(str, [self.case_1.pk, self.another_case_2.pk]))}
        response = self.client.post(self.cases_url, post_data)

        self.assert_quick_search_is_shown(response)
        self.assert_search_result(response)

    def test_normal_search(self):
        self.client.login(username=self.plan_tester.username, password='password')

        post_data = {'a': 'link_cases', 'action': 'search', 'search_mode': 'normal',
                     'case_id_set': ','.join(map(str, [self.case_1.pk, self.another_case_2.pk]))}
        response = self.client.post(self.cases_url, post_data)

        self.assert_normal_search_is_shown(response)
        self.assert_search_result(response)

    def test_missing_permission_to_link_cases(self):
        self.client.login(username=self.plan_tester.username, password='password')

        post_data = {'a': 'link_cases', 'action': 'add_to_plan',
                     'case': [self.another_case_1.pk, self.another_case_2.pk]}
        response = self.client.post(self.cases_url, post_data)
        self.assertContains(response, 'Permission Denied')

    def test_link_cases(self):
        self.client.login(username=self.plan_tester.username, password='password')

        user_should_have_perm(self.plan_tester, 'testcases.add_testcaseplan')

        post_data = {'a': 'link_cases', 'action': 'add_to_plan',
                     'case': [self.another_case_1.pk, self.another_case_2.pk]}
        response = self.client.post(self.cases_url, post_data)

        self.assertRedirects(
            response,
            reverse('plan-get', args=[self.plan.pk]),
            target_status_code=http_client.MOVED_PERMANENTLY)

        self.assertTrue(
            TestCasePlan.objects.filter(plan=self.plan, case=self.another_case_1).exists())
        self.assertTrue(
            TestCasePlan.objects.filter(plan=self.plan, case=self.another_case_2).exists())


class TestCloneView(BasePlanCase):
    """Test case for cloning a plan"""

    @classmethod
    def setUpTestData(cls):
        super(TestCloneView, cls).setUpTestData()

        cls.another_plan = TestPlanFactory(
            name='Another plan for test',
            author=cls.tester, owner=cls.tester,
            product=cls.product, product_version=cls.version)
        cls.another_case_1 = TestCaseFactory(
            author=cls.tester, default_tester=None,
            reviewer=cls.tester, plan=[cls.another_plan])
        cls.another_case_2 = TestCaseFactory(
            author=cls.tester, default_tester=None,
            reviewer=cls.tester, plan=[cls.another_plan])

        cls.third_plan = TestPlanFactory(
            name='Third plan for test',
            author=cls.tester, owner=cls.tester,
            product=cls.product, product_version=cls.version)
        cls.third_case_1 = TestCaseFactory(
            author=cls.tester, default_tester=None,
            reviewer=cls.tester, plan=[cls.third_plan])
        cls.third_case_2 = TestCaseFactory(
            author=cls.tester, default_tester=None,
            reviewer=cls.tester, plan=[cls.third_plan])

        cls.totally_new_plan = TestPlanFactory(
            name='Test clone plan with copying cases',
            author=cls.tester, owner=cls.tester,
            product=cls.product, product_version=cls.version)
        cls.case_maintain_original_author = TestCaseFactory(
            author=cls.tester, default_tester=None,
            reviewer=cls.tester, plan=[cls.totally_new_plan])
        cls.case_keep_default_tester = TestCaseFactory(
            author=cls.tester, default_tester=None,
            reviewer=cls.tester, plan=[cls.totally_new_plan])

        cls.plan_tester = User.objects.create_user(
            username='plan_tester',
            email='tester@example.com',
            password='password')
        user_should_have_perm(cls.plan_tester, 'testplans.add_testplan')
        cls.plan_clone_url = reverse('plans-clone')

    def test_refuse_if_missing_a_plan(self):
        self.client.login(username=self.plan_tester.username, password='password')

        data_missing_plan = {}  # No plan is passed
        response = self.client.get(self.plan_clone_url, data_missing_plan)
        self.assertContains(response, 'At least one plan is required by clone function')

    def test_refuse_if_give_nonexisting_plan(self):
        self.client.login(username=self.plan_tester.username, password='password')

        response = self.client.get(self.plan_clone_url, {'plan': 99999})
        self.assertContains(response, 'The plan you specify does not exist in database')

    def test_open_clone_page_to_clone_one_plan(self):
        self.client.login(username=self.plan_tester.username, password='password')

        response = self.client.get(self.plan_clone_url, {'plan': self.plan.pk})

        self.assertContains(
            response,
            '<label class="strong" for="id_name">New Plan Name</label>',
            html=True)

        self.assertContains(
            response,
            '<input id="id_name" name="name" type="text" value="Copy of {}">'.format(
                self.plan.name),
            html=True)

    def test_open_clone_page_to_clone_multiple_plans(self):
        self.client.login(username=self.plan_tester.username, password='password')

        response = self.client.get(self.plan_clone_url,
                                   {'plan': [self.plan.pk, self.another_plan.pk]})

        plans_li = ['''<li>
    <span class="lab-50">{}</span>
    <span class="lab-100">{}</span>
    <span>
        <a href="" title="{} ({})">{}</a>
    </span>
</li>'''.format(plan.pk, plan.type, plan.name, plan.author.email, plan.name)
            for plan in (self.plan, self.another_plan)]

        self.assertContains(
            response,
            '<ul class="ul-no-format">{}</ul>'.format(''.join(plans_li)),
            html=True)

    def verify_cloned_plan(self, original_plan, cloned_plan,
                           link_cases=True, copy_cases=None,
                           maintain_case_orignal_author=None,
                           keep_case_default_tester=None):
        self.assertEqual('Copy of {}'.format(original_plan.name), cloned_plan.name)
        self.assertEqual(Product.objects.get(pk=self.product.pk), cloned_plan.product)
        self.assertEqual(Version.objects.get(pk=self.version.pk), cloned_plan.product_version)

        # Verify option set_parent
        self.assertEqual(TestPlan.objects.get(pk=original_plan.pk), cloned_plan.parent)

        # Verify option copy_texts
        self.assertEqual(cloned_plan.text.count(), original_plan.text.count())
        for copied_text, original_text in zip(cloned_plan.text.all(),
                                              original_plan.text.all()):
            self.assertEqual(copied_text.plan_text_version, original_text.plan_text_version)
            self.assertEqual(copied_text.author, original_text.author)
            self.assertEqual(copied_text.create_date, original_text.create_date)
            self.assertEqual(copied_text.plan_text, original_text.plan_text)

        # Verify option copy_attachments
        for attachment in original_plan.attachment.all():
            added = TestPlanAttachment.objects.filter(
                plan=cloned_plan, attachment=attachment).exists()
            self.assertTrue(added)

        # Verify option copy_environment_groups
        for env_group in original_plan.env_group.all():
            added = TCMSEnvPlanMap.objects.filter(plan=cloned_plan, group=env_group).exists()
            self.assertTrue(added)

        # Verify options link_testcases and copy_testcases
        if link_cases and not copy_cases:
            for case in original_plan.case.all():
                is_case_linked = TestCasePlan.objects.filter(plan=cloned_plan, case=case).exists()
                self.assertTrue(is_case_linked)

        if link_cases and copy_cases:
            # Ensure cases of original plan are not linked to cloned plan
            for case in original_plan.case.all():
                original_case_not_linked_to_cloned_plan = TestCasePlan.objects.filter(
                    plan=cloned_plan, case=case).exists()
                self.assertFalse(original_case_not_linked_to_cloned_plan)

            self.assertEqual(cloned_plan.case.count(), original_plan.case.count())

            # Verify if case' author and default tester are set properly
            for original_case, copied_case in zip(original_plan.case.all(),
                                                  cloned_plan.case.all()):
                if maintain_case_orignal_author:
                    self.assertEqual(original_case.author, copied_case.author)
                else:
                    me = self.plan_tester
                    self.assertEqual(me, copied_case.author)

                if keep_case_default_tester:
                    self.assertEqual(original_case.default_tester, copied_case.default_tester)
                else:
                    me = self.plan_tester
                    self.assertEqual(me, copied_case.default_tester)

    def test_clone_a_plan_with_default_options(self):
        post_data = {
            'name': self.third_plan.make_cloned_name(),
            'plan': self.third_plan.pk,
            'product': self.product.pk,
            'product_version': self.version.pk,
            'set_parent': 'on',
            'copy_texts': 'on',
            'copy_attachments': 'on',
            'copy_environment_groups': 'on',
            'link_testcases': 'on',
            'maintain_case_orignal_author': 'on',
            'keep_case_default_tester': 'on',
            'submit': 'Clone',
        }
        self.client.login(username=self.plan_tester.username, password='password')
        response = self.client.post(self.plan_clone_url, post_data)

        cloned_plan = TestPlan.objects.get(name=self.third_plan.make_cloned_name())

        self.assertRedirects(
            response,
            reverse('plan-get', args=[cloned_plan.pk]),
            target_status_code=http_client.MOVED_PERMANENTLY)

        self.verify_cloned_plan(self.third_plan, cloned_plan)

    def test_clone_a_plan_by_copying_cases(self):
        post_data = {
            'name': self.totally_new_plan.make_cloned_name(),
            'plan': self.totally_new_plan.pk,
            'product': self.product.pk,
            'product_version': self.version.pk,
            'set_parent': 'on',
            'copy_texts': 'on',
            'copy_attachments': 'on',
            'copy_environment_groups': 'on',
            'link_testcases': 'on',
            'maintain_case_orignal_author': 'on',
            'keep_case_default_tester': 'on',
            'submit': 'Clone',

            'copy_testcases': 'on',
        }
        self.client.login(username=self.plan_tester.username, password='password')
        self.client.post(self.plan_clone_url, post_data)
        cloned_plan = TestPlan.objects.get(name=self.totally_new_plan.make_cloned_name())
        self.verify_cloned_plan(self.totally_new_plan, cloned_plan,
                                copy_cases=True,
                                maintain_case_orignal_author=True,
                                keep_case_default_tester=True)

    def test_clone_a_plan_by_setting_me_to_copied_cases_author_default_tester(self):
        post_data = {
            'name': self.totally_new_plan.make_cloned_name(),
            'plan': self.totally_new_plan.pk,
            'product': self.product.pk,
            'product_version': self.version.pk,
            'set_parent': 'on',
            'copy_texts': 'on',
            'copy_attachments': 'on',
            'copy_environment_groups': 'on',
            'link_testcases': 'on',
            'submit': 'Clone',

            'copy_testcases': 'on',
            # Do not pass maintain_case_orignal_author and keep_case_default_tester
        }
        self.client.login(username=self.plan_tester.username, password='password')
        self.client.post(self.plan_clone_url, post_data)
        cloned_plan = TestPlan.objects.get(name=self.totally_new_plan.make_cloned_name())
        self.verify_cloned_plan(self.totally_new_plan, cloned_plan, copy_cases=True)

    def test_clone_multiple_plans_with_default_options(self):
        post_data = {
            'plan': [self.plan.pk, self.another_plan.pk],
            'product': self.product.pk,
            'product_version': self.version.pk,
            'set_parent': 'on',
            'copy_texts': 'on',
            'copy_attachments': 'on',
            'copy_environment_groups': 'on',
            'link_testcases': 'on',
            'maintain_case_orignal_author': 'on',
            'keep_case_default_tester': 'on',
            'submit': 'Clone',
        }
        self.client.login(username=self.plan_tester.username, password='password')
        response = self.client.post(self.plan_clone_url, post_data)

        url_querystr = urllib.parse.urlencode({
            'action': 'search',
            'product': self.product.pk,
            'product_version': self.version.pk
        })
        self.assertRedirects(
            response,
            '{}?{}'.format(reverse('plans-all'), url_querystr))

        for origin_plan in (self.plan, self.another_plan):
            cloned_plan = TestPlan.objects.get(name=origin_plan.make_cloned_name())
            self.verify_cloned_plan(origin_plan, cloned_plan)


class TestAJAXSearch(BasePlanCase):
    """Test ajax_search view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestAJAXSearch, cls).setUpTestData()

        # Add more plans for testing search
        for i in range(25):
            TestPlanFactory(author=cls.tester,
                            owner=cls.tester,
                            product=cls.product,
                            product_version=cls.version)

        # So far, each test has 26 plans

        cls.search_url = reverse('plans-ajax-search')

        # By default, search active plans. Search by other fields if needed,
        # copy this dict and add other fields.
        cls.search_data = {
            # Search plans
            'is_active': 'on',

            # DataTable properties: pagination and sorting
            'sEcho': 1,
            'iDisplayStart': 0,
            'iDisplayLength': 3,
            'iSortCol_0': 1,
            'sSortDir_0': 'asc',
            'iSortingCols': 1,
            # In the view, first column is not sortable.
            'bSortable_0': 'false',
            'bSortable_1': 'true',
            'bSortable_2': 'true',
            'bSortable_3': 'true',
            'bSortable_4': 'true',
        }

    def test_emtpy_plans(self):
        response = self.client.get(self.search_url, {})

        data = json_loads(response.content)

        self.assertEqual(0, data['sEcho'])
        self.assertEqual(0, data['iTotalRecords'])
        self.assertEqual(0, data['iTotalDisplayRecords'])
        self.assertEqual([], data['aaData'])

    def test_get_first_page_order_by_pk(self):
        search_data = self.search_data.copy()

        response = self.client.get(self.search_url, search_data)

        data = json_loads(response.content)

        plans_count = TestPlan.objects.count()
        self.assertEqual(1, data['sEcho'])
        self.assertEqual(plans_count, data['iTotalRecords'])
        self.assertEqual(plans_count, data['iTotalDisplayRecords'])
        self.assertEqual(search_data['iDisplayLength'], len(data['aaData']))

        expected_plans = TestPlan.objects.all()[0:3]

        for i, plan in enumerate(expected_plans):
            self.assertEquals(
                "<a href='{}'>{}</a>".format(plan.get_absolute_url(), plan.pk),
                data['aaData'][i]['1'])

    def test_get_last_page_order_by_name(self):
        search_data = self.search_data.copy()
        plans_count = TestPlan.objects.count()
        # To request last page
        search_data['iDisplayStart'] = int((round(plans_count / 3.0) - 1) * 3)
        search_data['iSortCol_0'] = 2

        response = self.client.get(self.search_url, search_data)

        data = json_loads(response.content)

        self.assertEqual(1, data['sEcho'])
        self.assertEqual(plans_count, data['iTotalRecords'])
        self.assertEqual(plans_count, data['iTotalDisplayRecords'])
        self.assertEqual(2, len(data['aaData']))

        expected_plans = TestPlan.objects.order_by('name')[
            search_data['iDisplayStart']:plans_count
        ]

        for i, plan in enumerate(expected_plans):
            self.assertEquals(
                "<a href='{}'>{}</a>".format(plan.get_absolute_url(), plan.pk),
                data['aaData'][i]['1'])

    def test_get_second_page_order_by_pk_desc(self):
        search_data = self.search_data.copy()
        # To request second page
        search_data['iDisplayStart'] = 3
        search_data['sSortDir_0'] = 'desc'

        response = self.client.get(self.search_url, search_data)

        data = json_loads(response.content)

        plans_count = TestPlan.objects.count()
        self.assertEqual(1, data['sEcho'])
        self.assertEqual(plans_count, data['iTotalRecords'])
        self.assertEqual(plans_count, data['iTotalDisplayRecords'])
        self.assertEqual(search_data['iDisplayLength'], len(data['aaData']))

        expected_plans = TestPlan.objects.order_by('-pk')[3:6]

        for i, plan in enumerate(expected_plans):
            self.assertEquals(
                "<a href='{}'>{}</a>".format(plan.get_absolute_url(), plan.pk),
                data['aaData'][i]['1'])
