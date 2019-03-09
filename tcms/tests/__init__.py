# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

from http import HTTPStatus

from django import test
from django.conf import settings
from django.contrib.auth.models import Permission

from tcms.testruns.models import TestExecutionStatus
from tcms.testcases.models import TestCaseStatus
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestExecutionFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory
from tcms.tests.factories import BuildFactory


def user_should_have_perm(user, perm):
    if isinstance(perm, str):
        try:
            app_label, codename = perm.split('.')
        except ValueError:
            raise ValueError('%s is not valid. Should be in format app_label.perm_codename')
        else:
            if not app_label or not codename:
                raise ValueError('Invalid app_label or codename')
            get_permission = Permission.objects.get
            user.user_permissions.add(
                get_permission(content_type__app_label=app_label, codename=codename))
    elif isinstance(perm, Permission):
        user.user_permissions.add(perm)
    else:
        raise TypeError('perm should be an instance of either str or Permission')


def remove_perm_from_user(user, perm):
    """Remove a permission from an user"""

    if isinstance(perm, str):
        try:
            app_label, codename = perm.split('.')
        except ValueError:
            raise ValueError('%s is not valid. Should be in format app_label.perm_codename')
        else:
            if not app_label or not codename:
                raise ValueError('Invalid app_label or codename')
            get_permission = Permission.objects.get
            user.user_permissions.remove(
                get_permission(content_type__app_label=app_label, codename=codename))
    elif isinstance(perm, Permission):
        user.user_permissions.remove(perm)
    else:
        raise TypeError('perm should be an instance of either str or Permission')


def create_request_user(username=None, password=None):
    if username:
        user = UserFactory(username=username)
    else:
        user = UserFactory()
    if password:
        user.set_password(password)
    else:
        user.set_password('password')
    user.save()
    return user


class LoggedInTestCase(test.TestCase):
    """
        Test case class for logged-in users which also provides couple of
        helper assertion methods.
    """

    @classmethod
    def setUpTestData(cls):
        cls.tester = UserFactory()
        cls.tester.set_password('password')
        cls.tester.save()

    def setUp(self):
        """
            Login because by default we have GlobalLoginRequiredMiddleware enabled!
        """
        super().setUp()
        self.client.login(username=self.tester.username,  # nosec:B106:hardcoded_password_funcarg
                          password='password')

    # todo: create a lint plugin for that to enforce using the helper
    def assert404(self, response):
        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)

    # todo: create a lint plugin for that to enforce using the helper
    def assertJsonResponse(self, response, expected, status_code=200):
        self.assertEqual(status_code, response.status_code)
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            expected)


class BasePlanCase(LoggedInTestCase):
    """Base test case by providing essential Plan and Case objects used in tests"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.case_status_confirmed = TestCaseStatus.objects.get(name='CONFIRMED')
        cls.case_status_proposed = TestCaseStatus.objects.get(name='PROPOSED')

        cls.product = ProductFactory(name='Kiwi')
        cls.version = VersionFactory(value='0.1', product=cls.product)

        cls.plan = TestPlanFactory(
            author=cls.tester,
            product=cls.product,
            product_version=cls.version)

        cls.case = TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            case_status=cls.case_status_confirmed,
            plan=[cls.plan])
        cls.case.save()  # will generate history object

        cls.case_1 = TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            case_status=cls.case_status_confirmed,
            plan=[cls.plan])
        cls.case_1.save()  # will generate history object

        cls.case_2 = TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            case_status=cls.case_status_confirmed,
            plan=[cls.plan])
        cls.case_2.save()  # will generate history object

        cls.case_3 = TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            case_status=cls.case_status_confirmed,
            plan=[cls.plan])
        cls.case_3.save()  # will generate history object

        cls.case_4 = TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            case_status=cls.case_status_confirmed,
            plan=[cls.plan])
        cls.case_4.save()  # will generate history object

        cls.case_5 = TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            case_status=cls.case_status_confirmed,
            plan=[cls.plan])
        cls.case_5.save()  # will generate history object

        cls.case_6 = TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            case_status=cls.case_status_confirmed,
            plan=[cls.plan])
        cls.case_6.save()  # will generate history object


class BaseCaseRun(BasePlanCase):
    """Base test case containing test run and case runs"""

    @classmethod
    def setUpTestData(cls):
        super(BaseCaseRun, cls).setUpTestData()

        # todo: we need a linter to find all places where we get statuses
        # by hard-coded names instead of class based attribute constants!
        cls.status_idle = TestExecutionStatus.objects.get(name='IDLE')

        cls.build = BuildFactory(product=cls.product)

        cls.test_run = TestRunFactory(product_version=cls.version,
                                      plan=cls.plan,
                                      build=cls.build,
                                      manager=cls.tester,
                                      default_tester=cls.tester)

        executions = []
        for i, case in enumerate((cls.case_1, cls.case_2, cls.case_3), 1):
            executions.append(TestExecutionFactory(assignee=cls.tester,
                                                   run=cls.test_run,
                                                   build=cls.build,
                                                   status=cls.status_idle,
                                                   case=case, sortkey=i * 10))

        # used in other tests as well
        cls.execution_1 = executions[0]
        cls.execution_2 = executions[1]
        cls.execution_3 = executions[2]

        cls.test_run_1 = TestRunFactory(product_version=cls.version,
                                        plan=cls.plan,
                                        build=cls.build,
                                        manager=cls.tester,
                                        default_tester=cls.tester)

        # create a few more TestExecution objects
        for i, case in enumerate((cls.case_4, cls.case_5, cls.case_6), 1):
            executions.append(TestExecutionFactory(assignee=cls.tester,
                                                   tested_by=cls.tester,
                                                   run=cls.test_run_1,
                                                   build=cls.build,
                                                   status=cls.status_idle,
                                                   case=case, sortkey=i * 10))
        # used in other tests as well
        cls.execution_4 = executions[3]
        cls.execution_5 = executions[4]
        cls.execution_6 = executions[5]
