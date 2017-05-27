# -*- coding: utf-8 -*-

from django import test
from django.contrib.auth.models import Permission

from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestCaseRunFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory
from tcms.tests.factories import TestBuildFactory

__all__ = (
    'user_should_have_perm',
    'remove_perm_from_user',
    'BasePlanCase',
)


def user_should_have_perm(user, perm):
    if isinstance(perm, basestring):
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
        raise TypeError('perm should be an instance of either basestring or Permission')


def remove_perm_from_user(user, perm):
    """Remove a permission from an user"""

    if isinstance(perm, basestring):
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
        raise TypeError('perm should be an instance of either basestring or Permission')


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


class BasePlanCase(test.TestCase):
    """Base test case by providing essential Plan and Case objects used in tests"""

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(name='Kiwi')
        cls.version = VersionFactory(value='0.1', product=cls.product)
        cls.tester = UserFactory()
        cls.plan = TestPlanFactory(author=cls.tester, owner=cls.tester,
                                   product=cls.product, product_version=cls.version)
        cls.case = TestCaseFactory(author=cls.tester, default_tester=None, reviewer=cls.tester,
                                   plan=[cls.plan])
        cls.case_1 = TestCaseFactory(author=cls.tester, default_tester=None, reviewer=cls.tester,
                                     plan=[cls.plan])
        cls.case_2 = TestCaseFactory(author=cls.tester, default_tester=None, reviewer=cls.tester,
                                     plan=[cls.plan])
        cls.case_3 = TestCaseFactory(author=cls.tester, default_tester=None, reviewer=cls.tester,
                                     plan=[cls.plan])


class BaseCaseRun(BasePlanCase):
    """Base test case containing test run and case runs"""

    @classmethod
    def setUpTestData(cls):
        super(BaseCaseRun, cls).setUpTestData()

        cls.build = TestBuildFactory(product=cls.product)

        cls.test_run = TestRunFactory(product_version=cls.version,
                                      plan=cls.plan,
                                      manager=cls.tester,
                                      default_tester=cls.tester)
        cls.case_run_1 = TestCaseRunFactory(assignee=cls.tester,
                                            tested_by=cls.tester,
                                            run=cls.test_run,
                                            case=cls.case_1,
                                            build=cls.build,
                                            sortkey=101)
        cls.case_run_2 = TestCaseRunFactory(assignee=cls.tester,
                                            tested_by=cls.tester,
                                            run=cls.test_run,
                                            case=cls.case_2,
                                            build=cls.build,
                                            sortkey=200)
        cls.case_run_3 = TestCaseRunFactory(assignee=cls.tester,
                                            tested_by=cls.tester,
                                            run=cls.test_run,
                                            case=cls.case_3,
                                            build=cls.build,
                                            sortkey=300)
