# -*- coding: utf-8 -*-

from django import test

from tcms.xmlrpc.api import testcase as XmlrpcTestCase
from tcms.xmlrpc.tests.utils import make_http_request
from tcms.xmlrpc.tests.utils import user_should_have_perm

from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import UserFactory

__all__ = (
    'TestNotificationRemoveCC',
)


class TestNotificationRemoveCC(test.TestCase):
    """ Tests the XMLRPM testcase.notication_remove_cc method """

    @classmethod
    def setUpClass(cls):
        super(TestNotificationRemoveCC, cls).setUpClass()

        cls.user = UserFactory()
        cls.http_req = make_http_request(user=cls.user)
        perm_name = 'testcases.change_testcase'
        user_should_have_perm(cls.http_req.user, perm_name)

        cls.default_cc = 'example@MrSenko.com'
        cls.testcase = TestCaseFactory()
        cls.testcase.emailing.add_cc(cls.default_cc)

    @classmethod
    def tearDownClass(cls):
        cls.testcase.emailing.cc_list.all().delete()
        cls.testcase.delete()
        cls.user.delete()
        super(TestNotificationRemoveCC, cls).tearDownClass()

    def test_remove_existing_cc(self):
        # initially testcase has the default CC listed
        # and we issue XMLRPC request to remove the cc
        XmlrpcTestCase.notification_remove_cc(self.http_req, self.testcase.pk, [self.default_cc])

        # now verify that the CC email has been removed
        self.assertEqual(0, self.testcase.emailing.cc_list.count())
