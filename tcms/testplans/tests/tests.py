# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

from http import HTTPStatus

from django import test
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from uuslug import slugify

from tcms.management.models import Product, Version
from tcms.testcases.models import TestCasePlan, TestCaseStatus
from tcms.testplans.models import TestPlan
from tcms.tests import (BasePlanCase, remove_perm_from_user,
                        user_should_have_perm)
from tcms.tests.factories import (ClassificationFactory, PlanTypeFactory,
                                  ProductFactory, TestCaseFactory,
                                  TestPlanFactory, UserFactory, VersionFactory)


class BasePlanTest(test.TestCase):

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
                                        author=cls.user,
                                        product=cls.product,
                                        type=cls.plan_type)
        # add TestCases to plan with status CONFIRMED
        for _i in range(5):
            TestCaseFactory(plan=[cls.test_plan],
                            case_status=TestCaseStatus.objects.get(name='CONFIRMED'))

        # also add a few PROPOSED TestCases
        for _i in range(3):
            TestCaseFactory(plan=[cls.test_plan])

        cls.plan_id = cls.test_plan.pk
        cls.child_plan = TestPlanFactory(parent=cls.test_plan)

    def setUp(self):
        super().setUp()
        self.client.login(username=self.user.username,  # nosec:B106:hardcoded_password_funcarg
                          password='admin')


class PlanTests(BasePlanTest):

    def test_open_plans_search(self):
        location = reverse('plans-search')
        response = self.client.get(location)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_search_page_is_shown_with_get_parameter_used(self):
        response = self.client.get(reverse('plans-search'), {'product': self.product.pk})
        self.assertContains(response,
                            '<option value="%d" selected>%s</option>' % (self.product.pk,
                                                                         self.product.name),
                            html=True)

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
        self.assertContains(response, _('At least one test plan is required for print'))

    def test_plan_printable(self):
        location = reverse('plans-printable')
        response = self.client.post(location, {'plan': [self.test_plan.pk]})
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertContains(response, self.test_plan.name)
        self.assertContains(response, self.test_plan.text)

        confirmed = TestCaseStatus.objects.get(name='CONFIRMED')
        for case in self.test_plan.case.filter(case_status=confirmed):
            self.assertContains(response, case.summary)
            self.assertContains(response, case.text)

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

    def test_add_cases_sortkey_autoincrement(self):
        """
        When you add new cases, each new case should get a sortkey of the
        highest sortkey in the database + 10.

        The first case should get sortkey 0. The offset between the sortkeys is
        to leave space to insert cases in between without having to update all
        cases.
        """

        plan = TestPlanFactory()

        for sequence_no in range(3):
            case_plan = plan.add_case(TestCaseFactory())
            self.assertEqual(sequence_no * 10, case_plan.sortkey)

        # Check if you can still specify a sortkey manually to insert a case in
        # between the other cases.
        case_plan = plan.add_case(TestCaseFactory(), sortkey=15)
        self.assertEqual(15, case_plan.sortkey)


class TestSortCases(BasePlanCase):
    """Test case for sorting cases"""

    @classmethod
    def setUpTestData(cls):
        super(TestSortCases, cls).setUpTestData()
        cls.plan_tester = UserFactory(username='tester')
        cls.plan_tester.set_password('password')
        cls.plan_tester.save()
        user_should_have_perm(cls.plan_tester, 'testplans.change_testplan')

        cls.cases_url = reverse('plan-reorder-cases', args=[cls.plan.pk])

    def test_missing_cases_ids(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        response = self.client.post(self.cases_url)
        self.assertJsonResponse(
            response,
            {'rc': 1, 'response': 'At least one case is required to re-order.'})


class TestLinkCases(BasePlanCase):
    """Test case for linking cases from other plans"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.another_plan = TestPlanFactory(
            author=cls.tester,
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

        cls.plan_tester = UserFactory(username='tester')
        cls.plan_tester.set_password('password')
        cls.plan_tester.save()

        cls.search_cases_for_link_url = reverse('plan-search-cases-for-link',
                                                args=[cls.plan.pk])
        cls.link_cases_url = reverse('plan-link-cases', args=[cls.plan.pk])

        user_should_have_perm(cls.plan_tester, 'testcases.view_testcase')
        user_should_have_perm(cls.plan_tester, 'testplans.view_testplan')

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
        super().setUpTestData()

        cls.another_plan = TestPlanFactory(
            name='Another plan for test',
            author=cls.tester,
            product=cls.product, product_version=cls.version)
        cls.another_case_1 = TestCaseFactory(
            author=cls.tester, default_tester=None,
            reviewer=cls.tester, plan=[cls.another_plan])
        cls.another_case_2 = TestCaseFactory(
            author=cls.tester, default_tester=None,
            reviewer=cls.tester, plan=[cls.another_plan])

        cls.third_plan = TestPlanFactory(
            name='Third plan for test',
            author=cls.tester,
            product=cls.product, product_version=cls.version)
        cls.third_case_1 = TestCaseFactory(
            author=cls.tester, default_tester=None,
            reviewer=cls.tester, plan=[cls.third_plan])
        cls.third_case_2 = TestCaseFactory(
            author=cls.tester, default_tester=None,
            reviewer=cls.tester, plan=[cls.third_plan])

        cls.totally_new_plan = TestPlanFactory(
            name='Test clone plan with copying cases',
            author=cls.tester,
            product=cls.product, product_version=cls.version)
        cls.case_maintain_original_author = TestCaseFactory(
            author=cls.tester, default_tester=None,
            reviewer=cls.tester, plan=[cls.totally_new_plan])
        cls.case_keep_default_tester = TestCaseFactory(
            author=cls.tester, default_tester=None,
            reviewer=cls.tester, plan=[cls.totally_new_plan])

        cls.plan_tester = UserFactory()
        cls.plan_tester.set_password('password')
        cls.plan_tester.save()
        user_should_have_perm(cls.plan_tester, 'testplans.add_testplan')
        user_should_have_perm(cls.plan_tester, 'testplans.view_testplan')
        cls.plan_clone_url = reverse('plans-clone')

    def test_refuse_if_missing_a_plan(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        data_missing_plan = {}  # No plan is passed
        response = self.client.post(self.plan_clone_url, data_missing_plan, follow=True)
        self.assertContains(response, _('TestPlan is required'))

    def test_refuse_if_given_nonexisting_plan(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        response = self.client.post(self.plan_clone_url, {'plan': 99999}, follow=True)
        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)

    def test_open_clone_page_to_clone_one_plan(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')

        response = self.client.post(self.plan_clone_url, {'plan': self.plan.pk})

        self.assertContains(
            response,
            '<label class="col-md-1 col-lg-1" for="id_name">%s</label>' % _('Name'),
            html=True)

        self.assertContains(
            response,
            '<input type="text" id="id_name" name="name" value="{}" '
            'class="form-control" required>'.format(self.plan.make_cloned_name()),
            html=True)

    def verify_cloned_plan(self, original_plan, cloned_plan, copy_cases=None):
        self.assertEqual('Copy of {}'.format(original_plan.name), cloned_plan.name)
        self.assertEqual(cloned_plan.text, original_plan.text)
        self.assertEqual(Product.objects.get(pk=self.product.pk), cloned_plan.product)
        self.assertEqual(Version.objects.get(pk=self.version.pk), cloned_plan.product_version)

        self._verify_options(original_plan, cloned_plan, copy_cases)

    def _verify_options(self, original_plan, cloned_plan, copy_cases):
        # number of TCs should always be the same
        self.assertEqual(cloned_plan.case.count(), original_plan.case.count())

        # Verify option set_parent
        self.assertEqual(TestPlan.objects.get(pk=original_plan.pk), cloned_plan.parent)

        # Verify option copy_testcases
        for case in cloned_plan.case.all():
            is_case_linked = TestCasePlan.objects.filter(plan=original_plan, case=case).exists()

            if copy_cases:
                # Ensure cases of original plan are not linked to cloned plan
                self.assertFalse(is_case_linked)

                # verify author was updated
                self.assertEqual(self.plan_tester, case.author)
            else:
                self.assertTrue(is_case_linked)

            for original_case, copied_case in zip(original_plan.case.all(),
                                                  cloned_plan.case.all()):
                # default tester is always kept
                self.assertEqual(original_case.default_tester, copied_case.default_tester)

                if not copy_cases:
                    # when linking TCs author doesn't change
                    self.assertEqual(original_case.author, copied_case.author)

    def test_clone_a_plan_with_default_options(self):
        post_data = {
            'name': self.third_plan.make_cloned_name(),
            'plan': self.third_plan.pk,
            'product': self.product.pk,
            'version': self.version.pk,
            'set_parent': 'on',
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
            'version': self.version.pk,
            'set_parent': 'on',
            'submit': 'Clone',

            'copy_testcases': 'on',
        }
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')
        self.client.post(self.plan_clone_url, post_data)
        cloned_plan = TestPlan.objects.get(name=self.totally_new_plan.make_cloned_name())
        self.verify_cloned_plan(self.totally_new_plan, cloned_plan, copy_cases=True)

    def test_clone_a_plan_by_setting_me_to_copied_cases_author_default_tester(self):
        post_data = {
            'name': self.totally_new_plan.make_cloned_name(),
            'plan': self.totally_new_plan.pk,
            'product': self.product.pk,
            'version': self.version.pk,
            'set_parent': 'on',
            'submit': 'Clone',

            'copy_testcases': 'on',
        }
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')
        self.client.post(self.plan_clone_url, post_data)
        cloned_plan = TestPlan.objects.get(name=self.totally_new_plan.make_cloned_name())
        self.verify_cloned_plan(self.totally_new_plan, cloned_plan, copy_cases=True)
