# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

import json
from http import HTTPStatus
from uuslug import slugify
from urllib.parse import urlencode

from django import test
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse

from tcms.management.models import Product
from tcms.management.models import Version
from tcms.testcases.models import TestCasePlan, TestCaseStatus
from tcms.testplans.models import EnvPlanMap
from tcms.testplans.models import TestPlan
from tcms.core.contrib.auth.backends import initiate_user_with_default_setups

from tcms.tests.factories import ClassificationFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestCaseFactory, TestCaseTextFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import PlanTypeFactory
from tcms.tests.factories import EnvGroupFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory
from tcms.tests import BasePlanCase
from tcms.tests import remove_perm_from_user
from tcms.tests import user_should_have_perm


class TestPlanEnvironmentGroupTests(test.TestCase):
    """Test setting/editting ENV groups in Test Plans"""

    @classmethod
    def setUpTestData(cls):
        super(TestPlanEnvironmentGroupTests, cls).setUpTestData()

        cls.product = ProductFactory()
        cls.product_version = VersionFactory(product=cls.product)

        cls.env_group = EnvGroupFactory()
        cls.new_env_group = EnvGroupFactory(name='Laptop hardware')

        cls.tester = UserFactory()
        cls.tester.set_password('password')
        initiate_user_with_default_setups(cls.tester)

    def setUp(self):
        is_logged_in = self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        self.assertTrue(is_logged_in)

    def test_user_with_default_perms_can_create_testplan_and_set_env_group(self):
        # test for https://github.com/kiwitcms/Kiwi/issues/73
        url = reverse('plans-new')
        response = self.client.post(
            url,
            {
                'name': 'TP for Issue #73',
                'product': self.product.pk,
                'product_version': self.product_version.pk,
                'type': PlanTypeFactory().pk,
                'env_group': self.env_group.pk,
            },
            follow=True,
        )

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, ">%s</a>" % self.env_group.name)

    def test_user_with_default_perms_can_edit_tp_and_change_env_group(self):
        test_plan = TestPlanFactory(
            product=self.product,
            product_version=self.product_version,
            env_group=[self.env_group]
        )
        url = reverse('plan-edit', args=[test_plan.pk, ])

        response = self.client.post(
            url,
            {
                'name': 'NEW TEST PLAN NAME',
                'product': test_plan.product.pk,
                'product_version': test_plan.product_version.pk,
                'type': test_plan.type.pk,
                'env_group': self.new_env_group.pk,
                'text': "We've changed the ENV group setting",
            },
            follow=True,
        )

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, ">%s</a>" % self.new_env_group.name)


class PlanTests(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(username='admin', email='admin@example.com')
        cls.user.set_password('admin')
        cls.user.is_superuser = True
        cls.user.is_staff = True
        cls.user.save()

        cls.classification = ClassificationFactory(name='Auto')
        cls.product = ProductFactory(name='Kiwi', classification=cls.classification)
        cls.product_version = VersionFactory(value='0.1', product=cls.product)
        cls.plan_type = PlanTypeFactory()

        cls.test_plan = TestPlanFactory(name='another test plan for testing',
                                        product_version=cls.product_version,
                                        owner=cls.user,
                                        author=cls.user,
                                        product=cls.product,
                                        type=cls.plan_type)
        # add TestCases to plan with status CONFIRMED
        for i in range(5):
            case = TestCaseFactory(plan=[cls.test_plan],
                                   case_status=TestCaseStatus.objects.get(name='CONFIRMED'))
            TestCaseTextFactory(case=case)

        # also add a few PROPOSED TestCases
        for i in range(3):
            case = TestCaseFactory(plan=[cls.test_plan])
            TestCaseTextFactory(case=case)

        cls.plan_id = cls.test_plan.pk
        cls.child_plan = TestPlanFactory(parent=cls.test_plan)

    def setUp(self):
        super().setUp()
        self.client.login(username=self.user.username,  # nosec:B106:hardcoded_password_funcarg
                          password='admin')

    def test_open_plans_search(self):
        location = reverse('plans-all')
        response = self.client.get(location)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_search_plans(self):
        location = reverse('plans-all')
        response = self.client.get(location, {'action': 'search', 'type': self.test_plan.type.pk})
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_plan_treeview(self):
        location = reverse('plans-all')
        response = self.client.get(location, {'t': 'ajax', 'pk': self.test_plan.pk})

        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(1, len(data))
        self.assertEqual(self.test_plan.pk, data[0]['pk'])
        self.assertEqual(self.test_plan.get_full_url(), data[0]['get_full_url'])
        self.assertEqual(None, data[0]['parent'])
        self.assertEqual(1, data[0]['num_children'])

    def test_plan_new_get(self):
        location = reverse('plans-new')
        response = self.client.get(location, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_plan_details(self):
        location = reverse('test_plan_url_short', args=[self.plan_id])
        response = self.client.get(location)
        self.assertEqual(response.status_code, HTTPStatus.MOVED_PERMANENTLY)

        response = self.client.get(location, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_plan_edit(self):
        location = reverse('plan-edit', args=[self.plan_id])
        response = self.client.get(location)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_plan_printable_without_selected_plan(self):
        location = reverse('plans-printable')
        response = self.client.post(location, follow=True)
        self.assertContains(response, 'At least one test plan is required for print')

    def test_plan_printable(self):
        location = reverse('plans-printable')
        response = self.client.post(location, {'plan': [self.test_plan.pk]})
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertContains(response, self.test_plan.name)
        self.assertContains(response, self.test_plan.text)

        confirmed = TestCaseStatus.objects.get(name='CONFIRMED')
        for case in self.test_plan.case.filter(case_status=confirmed):
            self.assertContains(response, case.summary)
            # factory sets all 4
            self.assertContains(response, case.latest_text().setup)
            self.assertContains(response, case.latest_text().action)
            self.assertContains(response, case.latest_text().effect)
            self.assertContains(response, case.latest_text().breakdown)

    def test_plan_attachment(self):
        location = reverse('plan-attachment',
                           args=[self.plan_id])
        response = self.client.get(location)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_plan_history(self):
        # note: the history URL is generated on the fly and not accessible via
        # name
        location = "/admin/testplans/testplan/%d/history/" % self.plan_id
        response = self.client.get(location)
        self.assertEqual(response.status_code, HTTPStatus.OK)


class TestPlanModel(test.TestCase):
    """ Test some model operations directly without a view """

    @classmethod
    def setUpTestData(cls):
        cls.plan_1 = TestPlanFactory()
        cls.testcase_1 = TestCaseFactory()
        cls.testcase_2 = TestCaseFactory()

        cls.plan_1.add_case(cls.testcase_1)
        cls.plan_1.add_case(cls.testcase_2)

    def test_plan_delete_case(self):
        self.plan_1.delete_case(self.testcase_1)
        cases_left = TestCasePlan.objects.filter(plan=self.plan_1.pk)
        self.assertEqual(1, cases_left.count())
        self.assertEqual(self.testcase_2.pk, cases_left[0].case.pk)


class TestDeleteCasesFromPlan(BasePlanCase):
    """Test case for deleting cases from a plan"""

    @classmethod
    def setUpTestData(cls):
        super(TestDeleteCasesFromPlan, cls).setUpTestData()
        cls.plan_tester = User(username='tester')
        cls.plan_tester.set_password('password')
        cls.plan_tester.save()

        cls.cases_url = reverse('plan-delete-cases', args=[cls.plan.pk])

    def test_missing_cases_ids(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        response = self.client.post(self.cases_url)
        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(1, data['rc'])
        self.assertEqual('At least one case is required to delete.',
                         data['response'])

    def test_delete_cases(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        post_data = {'case': [self.case_1.pk, self.case_3.pk]}
        response = self.client.post(self.cases_url, post_data)
        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        self.assertEqual(0, data['rc'])
        self.assertEqual('ok', data['response'])
        self.assertFalse(self.plan.case.filter(
            pk__in=[self.case_1.pk, self.case_3.pk]).exists())

        # Assert action logs are recorded for plan and case correctly

        for case in (self.case_1, self.case_3):
            logs = case.log()
            first_log = logs.first()
            self.assertEqual(first_log.action, 'Remove from plan {}'.format(self.plan.pk))

            expected_log = 'Remove case {} from plan {}'.format(case.pk, self.plan.pk)
            self.assertTrue(self.plan.log().filter(action=expected_log).exists())


class TestSortCases(BasePlanCase):
    """Test case for sorting cases"""

    @classmethod
    def setUpTestData(cls):
        super(TestSortCases, cls).setUpTestData()
        cls.plan_tester = User(username='tester')
        cls.plan_tester.set_password('password')
        cls.plan_tester.save()

        cls.cases_url = reverse('plan-reorder-cases', args=[cls.plan.pk])

    def test_missing_cases_ids(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        response = self.client.post(self.cases_url)
        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(1, data['rc'])
        self.assertEqual('At least one case is required to re-order.', data['response'])

    def test_order_cases(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        post_data = {'case': [self.case_3.pk, self.case_1.pk]}
        response = self.client.post(self.cases_url, post_data)
        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        self.assertEqual({'rc': 0, 'response': 'ok'}, data)

        case_plan_rel = TestCasePlan.objects.get(plan=self.plan, case=self.case_3)
        self.assertEqual(10, case_plan_rel.sortkey)

        case_plan_rel = TestCasePlan.objects.get(plan=self.plan, case=self.case_1)
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

        cls.search_cases_for_link_url = reverse('plan-search-cases-for-link',
                                                args=[cls.plan.pk])
        cls.link_cases_url = reverse('plan-link-cases', args=[cls.plan.pk])

    def tearDown(self):
        # Ensure permission is removed whenever it was added during tests
        remove_perm_from_user(self.plan_tester, 'testcases.add_testcaseplan')

    def assert_quick_search_is_shown(self, response):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        self.assertContains(
            response,
            '<li class="profile_tab_active" id="quick_tab">')

    def assert_normal_search_is_shown(self, response):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        self.assertContains(
            response,
            '<li class="profile_tab_active" id="normal_tab">')

    def test_show_quick_search_by_default(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        response = self.client.post(self.search_cases_for_link_url, {})
        self.assert_quick_search_is_shown(response)

    def assert_search_result(self, response):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        self.assertContains(
            response,
            '<a href="{}">{}</a>'.format(
                reverse('testcases-get', args=[self.another_case_2.pk]),
                self.another_case_2.pk))

        # Assert: Do not list case that already belongs to the plan
        self.assertNotContains(
            response,
            '<a href="{}">{}</a>'.format(
                reverse('testcases-get', args=[self.case_2.pk]),
                self.case_2.pk))

    def test_quick_search(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        post_data = {
            'search_mode': 'quick',
            'case_id_set': ','.join(
                map(str, [self.case_1.pk, self.another_case_2.pk]))
        }
        response = self.client.post(self.search_cases_for_link_url, post_data)

        self.assert_quick_search_is_shown(response)
        self.assert_search_result(response)

    def test_normal_search(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        post_data = {
            'search_mode': 'normal',
            'case_id_set': ','.join(
                map(str, [self.case_1.pk, self.another_case_2.pk]))
        }
        response = self.client.post(self.search_cases_for_link_url, post_data)

        self.assert_normal_search_is_shown(response)
        self.assert_search_result(response)

    def test_link_cases(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        user_should_have_perm(self.plan_tester, 'testcases.add_testcaseplan')

        post_data = {
            'case': [self.another_case_1.pk, self.another_case_2.pk]
        }
        response = self.client.post(self.link_cases_url, post_data)
        self.assertRedirects(
            response,
            reverse('test_plan_url', args=[self.plan.pk, slugify(self.plan.name)]))

        self.assertTrue(
            TestCasePlan.objects.filter(
                plan=self.plan, case=self.another_case_1).exists())
        self.assertTrue(
            TestCasePlan.objects.filter(
                plan=self.plan, case=self.another_case_2).exists())


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

        cls.plan_tester = User.objects.create_user(  # nosec:B106:hardcoded_password_funcarg
            username='plan_tester',
            email='tester@example.com',
            password='password')
        user_should_have_perm(cls.plan_tester, 'testplans.add_testplan')
        cls.plan_clone_url = reverse('plans-clone')

    def test_refuse_if_missing_a_plan(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        data_missing_plan = {}  # No plan is passed
        response = self.client.get(self.plan_clone_url, data_missing_plan, follow=True)
        self.assertContains(response, 'At least one TestPlan is required')

    def test_refuse_if_given_nonexisting_plan(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        response = self.client.get(self.plan_clone_url, {'plan': 99999}, follow=True)
        self.assertContains(response, 'TestPlan(s) "%s" do not exist' % ['99999'])

    def test_open_clone_page_to_clone_one_plan(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

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
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        response = self.client.get(self.plan_clone_url,
                                   {'plan': [self.plan.pk, self.another_plan.pk]})

        self.assertContains(response, '<ul class="ul-no-format">')
        for plan in [self.plan, self.another_plan]:
            plan_li = """<li>
    <span class="lab-50">{}</span>
    <span class="lab-100">{}</span>
    <span>
        <a href="{}">{}</a>
    </span>
</li>""".format(plan.pk, plan.type, plan.get_full_url(), plan.name)
            self.assertContains(response, plan_li, html=True)

    def verify_cloned_plan(self, original_plan, cloned_plan,
                           link_cases=True, copy_cases=None,
                           maintain_case_orignal_author=None,
                           keep_case_default_tester=None):
        self.assertEqual('Copy of {}'.format(original_plan.name), cloned_plan.name)
        self.assertEqual(cloned_plan.text, original_plan.text)
        self.assertEqual(Product.objects.get(pk=self.product.pk), cloned_plan.product)
        self.assertEqual(Version.objects.get(pk=self.version.pk), cloned_plan.product_version)

        # Verify option set_parent
        self.assertEqual(TestPlan.objects.get(pk=original_plan.pk), cloned_plan.parent)

        # Verify option copy_environment_groups
        for env_group in original_plan.env_group.all():
            added = EnvPlanMap.objects.filter(plan=cloned_plan, group=env_group).exists()
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
            'copy_environment_groups': 'on',
            'link_testcases': 'on',
            'maintain_case_orignal_author': 'on',
            'keep_case_default_tester': 'on',
            'submit': 'Clone',
        }
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')
        response = self.client.post(self.plan_clone_url, post_data)

        cloned_plan = TestPlan.objects.get(name=self.third_plan.make_cloned_name())

        self.assertRedirects(
            response,
            reverse('test_plan_url_short', args=[cloned_plan.pk]),
            target_status_code=HTTPStatus.MOVED_PERMANENTLY)

        self.verify_cloned_plan(self.third_plan, cloned_plan)

    def test_clone_a_plan_by_copying_cases(self):
        post_data = {
            'name': self.totally_new_plan.make_cloned_name(),
            'plan': self.totally_new_plan.pk,
            'product': self.product.pk,
            'product_version': self.version.pk,
            'set_parent': 'on',
            'copy_environment_groups': 'on',
            'link_testcases': 'on',
            'maintain_case_orignal_author': 'on',
            'keep_case_default_tester': 'on',
            'submit': 'Clone',

            'copy_testcases': 'on',
        }
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')
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
            'copy_environment_groups': 'on',
            'link_testcases': 'on',
            'submit': 'Clone',

            'copy_testcases': 'on',
            # Do not pass maintain_case_orignal_author and keep_case_default_tester
        }
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')
        self.client.post(self.plan_clone_url, post_data)
        cloned_plan = TestPlan.objects.get(name=self.totally_new_plan.make_cloned_name())
        self.verify_cloned_plan(self.totally_new_plan, cloned_plan, copy_cases=True)

    def test_clone_multiple_plans_with_default_options(self):
        post_data = {
            'plan': [self.plan.pk, self.another_plan.pk],
            'product': self.product.pk,
            'product_version': self.version.pk,
            'set_parent': 'on',
            'copy_environment_groups': 'on',
            'link_testcases': 'on',
            'maintain_case_orignal_author': 'on',
            'keep_case_default_tester': 'on',
            'submit': 'Clone',
        }
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')
        response = self.client.post(self.plan_clone_url, post_data)

        url_querystr = urlencode({
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
        for i in range(24):
            TestPlanFactory(author=cls.tester,
                            owner=cls.tester,
                            product=cls.product,
                            product_version=cls.version)

        # test data for Issue #78
        # https://github.com/kiwitcms/Kiwi/issues/78
        cls.plan_bogus_name = TestPlanFactory(
            name=r"""A name with backslash(\), single quotes(') and double quotes(")""",
            author=cls.tester,
            owner=cls.tester,
            product=cls.product,
            product_version=cls.version)

        # So far, each test has 26 plans

        cls.search_url = reverse('plans-ajax_search')

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

    def test_search_all_runs(self):
        response = self.client.get(self.search_url, {'is_active': 'on'})

        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(0, data['sEcho'])
        self.assertEqual(TestPlan.objects.count(), data['iTotalRecords'])
        self.assertEqual(TestPlan.objects.count(), data['iTotalDisplayRecords'])
        for i, plan in enumerate(TestPlan.objects.all().order_by('pk')):
            self.assertEqual(
                "<a href='{}'>{}</a>".format(plan.get_full_url(), plan.pk),
                data['aaData'][i]['1'])

    def test_emtpy_plans(self):
        response = self.client.get(self.search_url, {})

        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        self.assertEqual(0, data['sEcho'])
        self.assertEqual(0, data['iTotalRecords'])
        self.assertEqual(0, data['iTotalDisplayRecords'])
        self.assertEqual([], data['aaData'])

    def test_get_first_page_order_by_pk(self):
        search_data = self.search_data.copy()

        response = self.client.get(self.search_url, search_data)

        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        plans_count = TestPlan.objects.count()
        self.assertEqual(1, data['sEcho'])
        self.assertEqual(plans_count, data['iTotalRecords'])
        self.assertEqual(plans_count, data['iTotalDisplayRecords'])
        self.assertEqual(search_data['iDisplayLength'], len(data['aaData']))

        expected_plans = TestPlan.objects.all().order_by('pk')[0:3]

        for i, plan in enumerate(expected_plans):
            self.assertEqual(
                "<a href='{}'>{}</a>".format(plan.get_full_url(), plan.pk),
                data['aaData'][i]['1'])

    def test_get_last_page_order_by_name(self):
        search_data = self.search_data.copy()
        plans_count = TestPlan.objects.count()
        # To request last page
        search_data['iDisplayStart'] = plans_count // 3 * 3
        search_data['iSortCol_0'] = 2

        response = self.client.get(self.search_url, search_data)

        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        self.assertEqual(1, data['sEcho'])
        self.assertEqual(plans_count, data['iTotalRecords'])
        self.assertEqual(plans_count, data['iTotalDisplayRecords'])
        self.assertEqual(2, len(data['aaData']))

        expected_plans = TestPlan.objects.order_by('name')[
            search_data['iDisplayStart']:plans_count
        ]

        for i, plan in enumerate(expected_plans):
            self.assertEqual(
                "<a href='{}'>{}</a>".format(plan.get_full_url(), plan.pk),
                data['aaData'][i]['1'])

    def test_get_second_page_order_by_pk_desc(self):
        search_data = self.search_data.copy()
        # To request second page
        search_data['iDisplayStart'] = 3
        search_data['sSortDir_0'] = 'desc'

        response = self.client.get(self.search_url, search_data)

        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        plans_count = TestPlan.objects.count()
        self.assertEqual(1, data['sEcho'])
        self.assertEqual(plans_count, data['iTotalRecords'])
        self.assertEqual(plans_count, data['iTotalDisplayRecords'])
        self.assertEqual(search_data['iDisplayLength'], len(data['aaData']))

        expected_plans = TestPlan.objects.order_by('-pk')[3:6]

        for i, plan in enumerate(expected_plans):
            self.assertEqual(
                "<a href='{}'>{}</a>".format(plan.get_full_url(), plan.pk),
                data['aaData'][i]['1'])
