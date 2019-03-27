# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors

from datetime import datetime

from django.urls import reverse
from django.conf import settings
from django.utils.translation import override

from tcms.testruns.models import TestExecutionStatus

from tcms.tests import BaseCaseRun
from tcms.tests import user_should_have_perm


class TestUpdateCaseRunStatusView(BaseCaseRun):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        user_should_have_perm(cls.tester, 'testruns.change_testexecution')
        cls.url = reverse('testruns-update_caserun_status')

    def test_update_status_positive_scenario(self):
        before_update = datetime.now()
        status_passed = TestExecutionStatus.objects.get(name=TestExecutionStatus.PASSED)
        post_data = {
            'status_id': status_passed.pk,
            'object_pk[]': [self.execution_1.pk, self.execution_2.pk],
        }

        response = self.client.post(self.url, post_data)

        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 0, 'response': 'ok'})

        for caserun in [self.execution_1, self.execution_2]:
            caserun.refresh_from_db()
            self.assertEqual(caserun.status_id, status_passed.pk)
            self.assertEqual(caserun.tested_by, self.tester)
            self.assertGreater(caserun.close_date, before_update)
            self.assertLess(caserun.close_date, datetime.now())

        # verify we didn't update the last TCR by mistake
        self.execution_3.refresh_from_db()
        with override('en'):
            self.assertEqual(self.execution_3.status.name, TestExecutionStatus.IDLE)
        self.assertNotEqual(self.execution_3.tested_by, self.tester)
        self.assertIsNone(self.execution_3.close_date)
