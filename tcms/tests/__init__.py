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
    def setUpClass(cls):
        super(BasePlanCase, cls).setUpClass()

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

    @classmethod
    def tearDownClass(cls):
        cls.case.plan.clear()
        cls.case.delete()
        cls.case_1.delete()
        cls.case_2.delete()
        cls.case_3.delete()
        cls.plan.delete()
        cls.plan.type.delete()
        cls.tester.delete()
        cls.version.delete()
        cls.product.delete()
        cls.product.classification.delete()
        super(BasePlanCase, cls).tearDownClass()
