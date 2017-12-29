# -*- coding: utf-8 -*-

import json
import http.client
import xml.etree.ElementTree as et
from urllib.parse import urlencode

from django import test
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.test.client import Client

from tcms.core.logs.models import TCMSLogModel
from tcms.management.models import Product
from tcms.management.models import Version
from tcms.testcases.models import TestCase
from tcms.testcases.models import TestCasePlan
from tcms.testplans.models import TCMSEnvPlanMap
from tcms.testplans.models import TestPlan
from tcms.testplans.models import TestPlanAttachment
from tcms.core.contrib.auth.backends import initiate_user_with_default_setups

from tcms.tests.factories import ComponentFactory
from tcms.tests.factories import ClassificationFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestPlanTypeFactory
from tcms.tests.factories import TestTagFactory
from tcms.tests.factories import TCMSEnvGroupFactory
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

        cls.env_group = TCMSEnvGroupFactory()
        cls.new_env_group = TCMSEnvGroupFactory(name='Laptop hardware')

        cls.tester = UserFactory()
        cls.tester.set_password('password')
        initiate_user_with_default_setups(cls.tester)

    def setUp(self):
        is_logged_in = self.client.login(username=self.tester.username, password='password')
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
                'type': TestPlanTypeFactory().pk,
                'env_group': self.env_group.pk,
            },
            follow=True,
        )

        self.assertEqual(http.client.OK, response.status_code)
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

        self.assertEqual(http.client.OK, response.status_code)
        self.assertContains(response, ">%s</a>" % self.new_env_group.name)


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
        cls.product = ProductFactory(name='Kiwi', classification=cls.classification)
        cls.product_version = VersionFactory(value='0.1', product=cls.product)
        cls.plan_type = TestPlanTypeFactory()

        cls.test_plan = TestPlanFactory(name='another test plan for testing',
                                        product_version=cls.product_version,
                                        owner=cls.user,
                                        author=cls.user,
                                        product=cls.product,
                                        type=cls.plan_type)
        cls.plan_id = cls.test_plan.pk
        cls.child_plan = TestPlanFactory(parent=cls.test_plan)

    def test_open_plans_search(self):
        location = reverse('plans-all')
        response = self.c.get(location)
        self.assertEqual(response.status_code, http.client.OK)

    def test_search_plans(self):
        location = reverse('plans-all')
        response = self.c.get(location, {'action': 'search', 'type': self.test_plan.type.pk})
        self.assertEqual(response.status_code, http.client.OK)

    def test_plan_treeview(self):
        location = reverse('plans-all')
        response = self.c.get(location, {'t': 'ajax', 'pk': self.test_plan.pk})

        self.assertEqual(response.status_code, http.client.OK)
        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(1, len(data))
        self.assertEqual(self.test_plan.pk, data[0]['pk'])
        self.assertEqual(self.test_plan.get_url_path(), data[0]['get_url_path'])
        self.assertEqual(None, data[0]['parent'])
        self.assertEqual(1, data[0]['num_children'])

    def test_plan_new_get(self):
        location = reverse('plans-new')
        response = self.c.get(location, follow=True)
        self.assertEqual(response.status_code, http.client.OK)

    def test_plan_details(self):
        location = reverse('test_plan_url_short', args=[self.plan_id])
        response = self.c.get(location)
        self.assertEqual(response.status_code, http.client.MOVED_PERMANENTLY)

        response = self.c.get(location, follow=True)
        self.assertEqual(response.status_code, http.client.OK)

    def test_plan_cases(self):
        location = reverse('plan-cases', args=[self.plan_id])
        response = self.c.get(location)
        self.assertEqual(response.status_code, http.client.OK)

    def test_plan_delete(self):
        tp_pk = self.test_plan.pk

        location = reverse('plan-delete', args=[tp_pk])
        response = self.c.get(location)
        self.assertEqual(response.status_code, http.client.OK)

        response = self.c.get(location, {'sure': 'no'})
        self.assertEqual(response.status_code, http.client.OK)

        response = self.c.get(location, {'sure': 'yes'})
        self.assertEqual(response.status_code, http.client.OK)
        deleted = not TestPlan.objects.filter(pk=tp_pk).exists()
        self.assertTrue(deleted,
                        'TestPlan {0} should be deleted. But, not.'.format(tp_pk))

    def test_plan_edit(self):
        location = reverse('plan-edit', args=[self.plan_id])
        response = self.c.get(location)
        self.assertEqual(response.status_code, http.client.OK)

    def test_plan_printable_without_selected_plan(self):
        location = reverse('plans-printable')
        response = self.c.get(location)
        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(response.context['info'], 'At least one target is required.')

    def test_plan_printable(self):
        location = reverse('plans-printable')
        response = self.c.get(location, {'plan': self.plan_id})
        self.assertEqual(response.status_code, http.client.OK)

        for test_plan in response.context['test_plans']:
            self.assertTrue(test_plan.pk > 0)
            self.assertTrue(test_plan.name is not '')
            self.assertTrue(test_plan.summary is not '')
            self.assertTrue(test_plan.latest_text.plan_text is not '')

            self.assertTrue(len(test_plan.result_set) > 0)
            for case in test_plan.result_set:
                self.assertTrue(case.case_id > 0)
                self.assertTrue(case.summary is not '')
                # factory sets all 4
                self.assertTrue(case.setup is not '')
                self.assertTrue(case.action is not '')
                self.assertTrue(case.effect is not '')
                self.assertTrue(case.breakdown is not '')

    def test_plan_attachment(self):
        location = reverse('plan-attachment',
                           args=[self.plan_id])
        response = self.c.get(location)
        self.assertEqual(response.status_code, http.client.OK)

    def test_plan_history(self):
        location = reverse('plan-text_history',
                           args=[self.plan_id])
        response = self.c.get(location)
        self.assertEqual(response.status_code, http.client.OK)

        response = self.c.get(location, {'plan_text_version': 1})
        self.assertEqual(response.status_code, http.client.OK)


class ExportTestPlanTests(test.TestCase):
    """ Test the export functionality! """

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(username='admin', email='admin@example.com')
        cls.user.set_password('admin')
        cls.user.is_superuser = True
        cls.user.save()

        cls.c = Client()
        cls.c.login(username='admin', password='admin')

        cls.classification = ClassificationFactory(name='Auto')
        cls.product = ProductFactory(name='Kiwi', classification=cls.classification)
        cls.product_version = VersionFactory(value='0.1', product=cls.product)
        cls.plan_type = TestPlanTypeFactory()

        cls.test_plan = TestPlanFactory(name='Test plan for testing exports',
                                        product_version=cls.product_version,
                                        owner=cls.user,
                                        author=cls.user,
                                        product=cls.product,
                                        type=cls.plan_type)

        # create test cases into the test plan
        cls.cases = []
        for i in range(10):
            case = TestCaseFactory(
                summary='test_case_number_%d' % i,
                author=cls.user,
                default_tester=None,
                reviewer=cls.user,
                plan=[cls.test_plan]
            )
            tag = TestTagFactory(name='tag_for_%s' % case.summary)
            component = ComponentFactory(name='component_for_%s' % case.summary)
            case.add_tag(tag)
            case.add_component(component)

            if i % 2 == 0:
                tag = TestTagFactory(name='second_tag_for_%s' % case.summary)
                component = ComponentFactory(name='second_component_for_%s' % case.summary)
                case.add_tag(tag)
                case.add_component(component)

            cls.cases.append(case)

    def test_export_returns_valid_xml_and_content(self):
        location = reverse('plans-export')
        response = self.c.get(location, {'plan': self.test_plan.pk})
        self.assertEqual(response.status_code, http.client.OK)

        xml_doc = response.content
        try:
            xml_doc = et.fromstring(xml_doc)
        except et.ParseError:
            self.fail('XML document exported from test plan is invalid.')

        for test_case in xml_doc.findall('testcase'):
            self.assertEqual('CONFIRMED', test_case.attrib['status'])

            for tp_ref in test_case.iter('testplan_reference'):
                self.assertEqual(tp_ref.text, self.test_plan.name)

            summary = test_case.findall('summary')[0].text
            case_number = int(summary.replace('test_case_number_', ''))

            # validate case tags
            tags = test_case.findall('tag')
            if case_number % 2 == 0:
                self.assertEqual(2, len(tags))
                self.assertEqual('second_tag_for_%s' % summary, tags[1].text)
            else:
                self.assertEqual(1, len(tags))
            self.assertEqual('tag_for_%s' % summary, tags[0].text)

            # validate case components
            components = test_case.findall('component')

            # each component has a product attribute
            for comp in components:
                self.assertTrue(comp.get('product') != '')

            if case_number % 2 == 0:
                self.assertEqual(2, len(components))
                self.assertEqual('second_component_for_%s' % summary, components[1].text.strip())
            else:
                self.assertEqual(1, len(components))
            self.assertEqual('component_for_%s' % summary, components[0].text.strip())

    def test_export_wo_parameters_returns_html_warning(self):
        location = reverse('plans-export')
        response = self.c.get(location)
        self.assertEqual(response.status_code, http.client.OK)
        self.assertIn('At least one target is required.', str(response.content,
                                                              encoding=settings.DEFAULT_CHARSET))


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
        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
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
        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(1, data['rc'])
        self.assertEqual('At least one case is required to delete.', data['response'])

    def test_delete_cases(self):
        self.client.login(username=self.plan_tester.username, password='password')

        post_data = {'a': 'delete_cases', 'case': [self.case_1.pk, self.case_3.pk]}
        response = self.client.post(self.cases_url, post_data)
        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

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
        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(1, data['rc'])
        self.assertEqual('At least one case is required to re-order.', data['response'])

    def test_order_cases(self):
        self.client.login(username=self.plan_tester.username, password='password')

        post_data = {'a': 'order_cases', 'case': [self.case_1.pk, self.case_3.pk]}
        response = self.client.post(self.cases_url, post_data)
        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

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
                reverse('testcases-get', args=[self.another_case_2.pk]),
                self.another_case_2.pk))

        # Assert: Do not list case that already belongs to the plan
        self.assertNotContains(
            response,
            '<a href="{}">{}</a>'.format(
                reverse('testcases-get', args=[self.case_2.pk]),
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
            reverse('test_plan_url_short', args=[self.plan.pk]),
            target_status_code=http.client.MOVED_PERMANENTLY)

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

        self.assertContains(response, '<ul class="ul-no-format">')
        for plan in [self.plan, self.another_plan]:
            plan_li = '''<li>
    <span class="lab-50">{}</span>
    <span class="lab-100">{}</span>
    <span>
        <a href="" title="{} ({})">{}</a>
    </span>
</li>'''.format(plan.pk, plan.type, plan.name, plan.author.email, plan.name)
            self.assertContains(response, plan_li, html=True)

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
            reverse('test_plan_url_short', args=[cloned_plan.pk]),
            target_status_code=http.client.MOVED_PERMANENTLY)

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
                "<a href='{}'>{}</a>".format(plan.get_absolute_url(), plan.pk),
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
                "<a href='{}'>{}</a>".format(plan.get_absolute_url(), plan.pk),
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
                "<a href='{}'>{}</a>".format(plan.get_absolute_url(), plan.pk),
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
                "<a href='{}'>{}</a>".format(plan.get_absolute_url(), plan.pk),
                data['aaData'][i]['1'])
