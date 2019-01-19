# -*- coding: utf-8 -*-

from http import HTTPStatus

from django import test
from django.urls import reverse

from tcms.testruns.models import TestCaseRunStatus

from tcms.tests.factories import ProductFactory
from tcms.tests.factories import BuildFactory
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import TestCaseRunFactory
from tcms.tests.factories import UserFactory


class TestingReportTestCase(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory()
        cls.tester = UserFactory()
        cls.tester.set_password('password')
        cls.tester.save()

    def setUp(self):
        super().setUp()
        self.client.login(username=self.tester.username,  # nosec:B106:hardcoded_password_funcarg
                          password='password')

    def test_report_view_loads(self):
        url = reverse('testing-report')
        response = self.client.get(url)

        self.assertEqual(HTTPStatus.OK, response.status_code)

    def test_generate_testing_report(self):
        # test for https://github.com/kiwitcms/Kiwi/issues/88
        #
        run = TestRunFactory()
        product_build = BuildFactory(product=run.plan.product)

        for status in TestCaseRunStatus.objects.all():
            TestCaseRunFactory(
                status=status,
                run=run,
                build=product_build)

        # Create an untested testcase run to assert that issue #88 does not arise.
        TestCaseRunFactory(
            tested_by=None,
            status=TestCaseRunStatus.objects.get(name='IDLE'),
            run=run,
            build=product_build,
        )

        url = reverse('testing-report')
        response = self.client.get(url, {
            'product': run.plan.product.pk,
            'report_type': 'per_build_report'
        })

        self.assertEqual(HTTPStatus.OK, response.status_code)
