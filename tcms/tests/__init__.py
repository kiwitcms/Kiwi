# -*- coding: utf-8 -*-

from django import test

from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory


class BasePlanCase(test.TestCase):
    """Base test case by providing essential Plan and Case objects used in tests"""

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(name='Nitrate')
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
