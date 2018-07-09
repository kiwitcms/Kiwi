# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import CategoryFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestNotificationRemoveCC(XmlrpcAPIBaseTest):
    """ Tests the XML-RPC testcase.notication_remove_cc method """

    def _fixture_setup(self):
        super(TestNotificationRemoveCC, self)._fixture_setup()

        self.default_cc = 'example@MrSenko.com'
        self.testcase = TestCaseFactory()
        self.testcase.emailing.add_cc(self.default_cc)

    def tearDown(self):
        super(TestNotificationRemoveCC, self).tearDown()
        self.rpc_client.Auth.logout()

    def test_remove_existing_cc(self):
        # initially testcase has the default CC listed
        # and we issue XMLRPC request to remove the cc
        self.rpc_client.TestCase.remove_notification_cc(self.testcase.pk, [self.default_cc])

        # now verify that the CC email has been removed
        self.assertEqual(0, self.testcase.emailing.cc_list.count())


class TestFilterCases(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestFilterCases, self)._fixture_setup()

        self.tester = UserFactory(username='great tester')
        self.product = ProductFactory(name='StarCraft')
        self.version = VersionFactory(value='0.1', product=self.product)
        self.plan = TestPlanFactory(name='Test product.get_cases',
                                    owner=self.tester, author=self.tester,
                                    product=self.product,
                                    product_version=self.version)
        self.case_category = CategoryFactory(product=self.product)
        self.cases_count = 10
        self.cases = [TestCaseFactory(category=self.case_category, author=self.tester,
                                      reviewer=self.tester, default_tester=None,
                                      plan=[self.plan])
                      for i in range(self.cases_count)]

    def test_filter_by_product_id(self):
        cases = self.rpc_client.TestCase.filter({'category__product': self.product.pk})
        self.assertIsNotNone(cases)
        self.assertEqual(len(cases), self.cases_count)


class TestUpdate(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestUpdate, self)._fixture_setup()

        self.testcase = TestCaseFactory()

    def test_update_text_and_product(self):
        case_text = self.testcase.latest_text()
        self.assertEqual('', case_text.setup)
        self.assertEqual('', case_text.breakdown)
        self.assertEqual('', case_text.action)
        self.assertEqual('', case_text.effect)
        self.assertNotEqual(self.api_user, case_text.author)

        # update the test case
        updated = self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                'summary': 'This was updated',
                'setup': 'new',
                'breakdown': 'new',
                'action': 'new',
                'effect': 'new',
            }
        )
        self.testcase.refresh_from_db()  # refresh before assertions

        self.assertEqual(updated['case_id'], self.testcase.pk)
        self.assertEqual('This was updated', self.testcase.summary)
        case_text = self.testcase.latest_text()  # grab text again
        self.assertEqual('new', case_text.setup)
        self.assertEqual('new', case_text.breakdown)
        self.assertEqual('new', case_text.action)
        self.assertEqual('new', case_text.effect)
        self.assertEqual(self.api_user, case_text.author)
