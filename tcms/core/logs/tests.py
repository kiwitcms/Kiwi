# -*- coding: utf-8 -*-

from django import test

from tcms.core.logs.views import TCMSLog
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import UserFactory


class Test_TCMSLog(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.tcms_log = TCMSLog(model=TestCaseFactory())
        cls.user = UserFactory()
        cls.actions = [
            "Test TCMLog with TestCase model",
            "Test TCMLog with TestCase model 2",
            "Test TCMLog with TestCase model 3"]

    def test_make_logs(self):
        for action in self.actions:
            self.tcms_log.make(self.user, action)

        logged_actions = self.tcms_log.list().values('action')
        for action in self.actions:
            self.assertIn({'action': action}, logged_actions)
