# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   Copyright (c) 2018 the Kiwi TCMS project. All rights reserved.
#   Author: Alexander Todorov <info@kiwitcms.org>
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from tcms_api.mutable import TestRun

from tcms_api.tests import BaseAPIClient_TestCase

from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import TestCaseRunFactory


class TestTestRunTests(BaseAPIClient_TestCase):
    def _fixture_setup(self):
        super(TestTestRunTests, self)._fixture_setup()

        self.testrun = TestRunFactory()
        for i in range(5):
            TestCaseRunFactory(run=self.testrun)

    def test_iterating_over_testrun_doesnt_crash(self):
        """
            https://github.com/kiwitcms/Kiwi/issues/194
        """
        i = 0
        for caserun in TestRun(self.testrun.pk):
            self.assertEqual('IDLE', caserun.status.name)
            i += 1
        self.assertEqual(5, i)
