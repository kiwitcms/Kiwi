# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, too-many-ancestors

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from tcms import tests
from tcms.tests import PermissionsTestCase, factories
from tcms.testruns.models import TestRun, TestExecutionStatus
from tcms.testcases.models import TestCaseStatus


class EditTestRunViewTestCase(PermissionsTestCase):
    """Test permissions for TestRun edit action"""

    permission_label = 'testruns.change_testrun'
    http_method_names = ['get', 'post']

    @classmethod
    def setUpTestData(cls):
        cls.test_run = factories.TestRunFactory(summary='Old summary')
        cls.url = reverse('testruns-edit', args=[cls.test_run.pk])
        cls.new_build = factories.BuildFactory(name='FastTest', product=cls.test_run.plan.product)
        intern = factories.UserFactory(username='intern',
                                       email='intern@example.com')
        cls.post_data = {
            'summary': 'New run summary',
            'build': cls.new_build.pk,
            'manager': cls.test_run.manager.email,
            'default_tester': intern.email,
            'notes': 'New run notes',
        }
        super().setUpTestData()

    def verify_get_with_permission(self):
        response = self.client.get(self.url)
        self.assertContains(
            response,
            '<input type="text" id="id_summary" name="summary" value="%s" class="form-control"'
            ' required>' % self.test_run.summary,
            html=True
        )
        self.assertContains(response, '<input id="id_manager" name="manager" value="%s"'
                                      ' type="text" class="form-control" placeholder='
                                      '"%s" required>'
                            % (self.test_run.manager, _('Username or email')), html=True)
        self.assertContains(response, _('Edit TestRun'))
        self.assertContains(response, 'testruns/js/mutable.js')

    def verify_post_with_permission(self):
        response = self.client.post(self.url, self.post_data)
        self.test_run.refresh_from_db()

        self.assertEqual(self.test_run.summary, 'New run summary')
        self.assertEqual(self.test_run.build, self.new_build)
        self.assertEqual(self.test_run.notes, 'New run notes')
        self.assertRedirects(
            response,
            reverse('testruns-get', args=[self.test_run.pk]))


class CreateTestRunViewTestCase(tests.PermissionsTestCase):
    permission_label = 'testruns.add_testrun'
    http_method_names = ['post']
    url = reverse('testruns-new')

    @classmethod
    def setUpTestData(cls):

        cls.plan = factories.TestPlanFactory()

        cls.build_fast = factories.BuildFactory(name='fast', product=cls.plan.product)

        cls.post_data = {
            'summary': cls.plan.name,
            'from_plan': cls.plan.pk,
            'build': cls.build_fast.pk,
            'notes': 'Create new test run',
            'POSTING_TO_CREATE': 'YES',
        }

        super().setUpTestData()

        cls.post_data['manager'] = cls.tester.email
        cls.post_data['default_tester'] = cls.tester.email

        case_status_confirmed = TestCaseStatus.get_confirmed()

        cls.case_1 = factories.TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            case_status=case_status_confirmed,
            plan=[cls.plan])
        cls.case_1.save()  # will generate history object

        cls.case_2 = factories.TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            case_status=case_status_confirmed,
            plan=[cls.plan])
        cls.case_2.save()  # will generate history object

        cls.post_data['case'] = [cls.case_1.pk, cls.case_2.pk]

    def verify_post_with_permission(self):
        response = self.client.post(self.url, self.post_data)
        last_run = TestRun.objects.last()

        self.assertRedirects(
            response,
            reverse('testruns-get', args=[last_run.pk]))

        self.assertEqual(self.plan.name, last_run.summary)
        self.assertEqual(self.plan, last_run.plan)
        self.assertEqual(self.plan.product_version, last_run.product_version)
        self.assertEqual(None, last_run.stop_date)
        self.assertEqual('Create new test run', last_run.notes)
        self.assertEqual(self.build_fast, last_run.build)
        self.assertEqual(self.tester, last_run.manager)
        self.assertEqual(self.tester, last_run.default_tester)
        for case, case_run in zip((self.case_1, self.case_2),
                                  last_run.case_run.order_by('case')):
            self.assertEqual(case, case_run.case)
            self.assertEqual(None, case_run.tested_by)
            self.assertEqual(self.tester, case_run.assignee)
            self.assertEqual(case.history.latest().history_id, case_run.case_text_version)
            self.assertEqual(last_run.build, case_run.build)
            self.assertEqual(None, case_run.close_date)


class MenuAddCommentItemTestCase(PermissionsTestCase):
    permission_label = 'django_comments.add_comment'
    http_method_names = ['get']

    @classmethod
    def setUpTestData(cls):
        cls.test_run = factories.TestRunFactory()

        cls.url = reverse('testruns-get', args=[cls.test_run.pk])
        cls.post_data = {'summary': 'mock', }
        super().setUpTestData()

        cls.add_comment_html = \
            '<a href="#" class="addBlue9 js-show-commentdialog">{0}</a>' \
            .format(_('Add'))

    def assert_on_testrun_page(self, response):
        self.assertContains(response, self.test_run.summary)
        self.assertContains(response, self.test_run.plan)
        self.assertContains(response, self.test_run.build)

    def verify_get_with_permission(self):
        response = self.client.get(self.url)
        self.assert_on_testrun_page(response)
        self.assertContains(response, self.add_comment_html, html=True)

    def verify_get_without_permission(self):
        response = self.client.get(self.url)
        self.assert_on_testrun_page(response)
        self.assertNotContains(response, self.add_comment_html, html=True)

class CreateTestStartCloneRunFromRunPage(tests.PermissionsTestCase):
    permission_label = 'testruns.add_testrun'
    http_method_names = ['post']
    url = reverse('testruns-new')

    @classmethod
    def setUpTestData(cls):
        cls.plan = factories.TestPlanFactory()
        cls.test_run = factories.TestRunFactory()

        cls.new_summary = 'Clone {} - {}'.format(cls.test_run.pk, cls.test_run.summary)

        cls.post_data = {
            'summary': cls.new_summary,
            'from_plan': cls.plan.pk,
            'product_id': cls.test_run.plan.product_id,
            'do': 'clone_run',
            'orig_run_id': cls.test_run.pk,
            'POSTING_TO_CREATE': 'YES',
            'product': cls.test_run.plan.product_id,
            'product_version': cls.test_run.product_version.pk,
            'build': cls.test_run.build.pk,
            'errata_id': '',
            'notes': '',
        }
        # post_data is the cloned data
        super().setUpTestData()
        executions = []
        cls.case_1 = factories.TestCaseFactory()
        cls.case_1.save()  # will generate history object
        cls.case_2 = factories.TestCaseFactory()
        cls.case_2.save()  # will generate history object

        cls.build = factories.BuildFactory()
        cls.status_idle = TestExecutionStatus.objects.get(name='IDLE')
        for i, case in enumerate((cls.case_1, cls.case_2), 1):
            executions.append(factories.TestExecutionFactory(assignee=cls.tester,
                                                       run=cls.test_run,
                                                       build=cls.build,
                                                       status=cls.status_idle,
                                                       case=case, sortkey=i * 10))

        # used in other tests as well
        cls.execution_1 = executions[0]
        cls.execution_2 = executions[1]

        cls.post_data['manager'] = cls.test_run.manager.email
        cls.post_data['default_tester'] = cls.tester.email
        cls.post_data['case'] = [cls.execution_1.pk, cls.execution_2.pk]
        cls.post_data['case_run_id'] = [cls.execution_1.pk, cls.execution_2.pk]

    def verify_post_without_permission(self):
        response = self.client.post(self.url, self.post_data)

        self.assertRedirects(
            response,
            reverse('tcms-login') + '?next=' + self.url)

    def verify_post_with_permission(self):
        response = self.client.post(self.url, self.post_data, follow=True)
        self.assertContains(response, '<input type="text" id="id_summary" name="summary" value="Clone')
        cloned_run = TestRun.objects.get(summary=self.new_summary)

        self.assertRedirects(
            response,
            reverse('testruns-get', args=[cloned_run.pk]))

        self.assert_cloned_run(cloned_run)

    def assert_cloned_run(self, cloned_run):
        # Assert clone settings result
        for origin_case_run, cloned_case_run in zip((self.execution_1, self.execution_2),
                                                    cloned_run.case_run.order_by('pk')):
            self.assertEqual(TestExecutionStatus.objects.get(name='IDLE'),
                             cloned_case_run.status)
            self.assertEqual(origin_case_run.assignee, cloned_case_run.assignee)
