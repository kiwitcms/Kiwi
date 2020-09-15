# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

from django import test
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile

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
            raise ValueError('"%s" should be: app_label.perm_codename' % perm) from None
        else:
            if not app_label or not codename:
                raise ValueError('Invalid app_label or codename')
            user.user_permissions.add(
                Permission.objects.get(content_type__app_label=app_label, codename=codename))
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
            raise ValueError('"%s" should be: app_label.perm_codename' % perm) from None
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
            Login because [view] permissions are required by default!
        """
        super().setUp()
        self.client.login(username=self.tester.username,  # nosec:B106:hardcoded_password_funcarg
                          password='password')

    def assertJsonResponse(self, response, expected, status_code=200):
        self.assertEqual(status_code, response.status_code)
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            expected)

    def attach_file_to(self, app_model_name, obj, file_obj=None):
        """
            Makes an attachment to use for testing.
        """
        app_name, model_name = app_model_name.split('.')

        add_url = reverse(
            "attachments:add",
            kwargs={
                "app_label": app_name,
                "model_name": model_name,
                "pk": obj.pk,
            },
        )

        if not file_obj:
            file_obj = SimpleUploadedFile(
                "a-test-filename.txt",
                b"Hello Test World",
                content_type="text/plain",
            )
        return self.client.post(
            add_url, {"attachment_file": file_obj}, follow=True
        )


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

        cls.status_idle = TestExecutionStatus.objects.filter(weight=0).first()

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


class PermissionsTestMixin:
    base_classes = ['PermissionsTestCase', 'APIPermissionsTestCase']
    http_method_names = []  # api, get or post
    permission_label = None

    # skip running if class called directly by test runner
    @classmethod
    def setUpClass(cls):
        if cls.__name__ in cls.base_classes:
            return
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        if cls.__name__ in cls.base_classes:
            return
        super().tearDownClass()

    def __call__(self, result=None):
        if self.__class__.__name__ in self.base_classes:
            return None

        return super().__call__(result)
    # end skip running

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.check_mandatory_attributes()

    @classmethod
    def check_mandatory_attributes(cls):
        """
            Make sure important class attributes are defined.
        """
        if not cls.permission_label:
            raise RuntimeError("Configure `permission_label` attribute for this test class")

        if not cls.http_method_names:
            raise RuntimeError("Configure `http_method_names` attribute for this test class")

    def verify_api_with_permission(self):
        self.fail('Not implemented')

    def verify_get_with_permission(self):
        self.fail('Not implemented')

    def verify_post_with_permission(self):
        self.fail('Not implemented')

    def verify_api_without_permission(self):
        self.fail('Not implemented')

    def verify_get_without_permission(self):
        self.fail('Not implemented')

    def verify_post_without_permission(self):
        self.fail('Not implemented')

    def test_with_permission(self):
        """
            Actual test method for positive scenario. Will validate
            all of the accepted methods by calling the
            verify_X_with_permission() method(s).
        """
        self.no_permissions_but(self.permission_label)
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        for method in self.http_method_names:
            function = getattr(self, 'verify_%s_with_permission' % method)
            function()

    def no_permissions_but(self, tested_permission):
        """
            Make sure self.tester has no other permissions but
            the one required!
        """
        self.tester.user_permissions.remove()
        user_should_have_perm(self.tester, tested_permission)

    def test_without_permission(self):
        """
            Actual test method for negative scenario. Will validate
            all of the accepted methods by calling the
            verify_X_without_permission() method(s).
        """
        self.all_permissions_except(self.permission_label)
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        for method in self.http_method_names:
            function = getattr(self, 'verify_%s_without_permission' % method)
            function()

    def all_permissions_except(self, tested_permission):
        """
            Make sure self.tester has all other permissions except
            the one required!
        """
        for perm in Permission.objects.all():
            user_should_have_perm(self.tester, perm)

        remove_perm_from_user(self.tester, tested_permission)


class PermissionsTestCase(PermissionsTestMixin, LoggedInTestCase):
    """Base class for all tests around view permissions"""

    url = None
    post_data = {}

    @classmethod
    def check_mandatory_attributes(cls):
        """
            Make sure important class attributes are defined.
        """
        super().check_mandatory_attributes()

        if not cls.url:
            raise RuntimeError("Configure `url` attribute for this test class")

        if 'post' in cls.http_method_names and not cls.post_data:
            raise RuntimeError("Configure `post_data` attribute for this test class")

        if 'post' not in cls.http_method_names and cls.post_data:
            raise RuntimeError("Unnecessary `post_data` attribute configured for non-POST test!")

    def verify_get_without_permission(self):
        """
            Implement all validation steps for GET self.url
            when self.tester does not have the appropriate permission.

            Default implementation asserts that user is redirected back
            to the login page!
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('tcms-login') + '?next=' + self.url)

    def verify_post_without_permission(self):
        """
            Implement all validation steps for POST self.url
            when self.tester does not have the appropriate permission.

            Default implementation asserts that user is redirected back
            to the login page!
        """
        response = self.client.post(self.url, self.post_data)
        self.assertRedirects(response, reverse('tcms-login') + '?next=' + self.url)

    def all_permissions_except(self, tested_permission):
        """
            Make sure self.tester has all other permissions except
            the one required!
        """
        for perm in Permission.objects.all():
            user_should_have_perm(self.tester, perm)

        remove_perm_from_user(self.tester, tested_permission)
