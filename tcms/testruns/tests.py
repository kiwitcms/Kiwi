# -*- coding: utf-8 -*-
import unittest
import random

from tcms.testruns import models
from tcms.core.utils.raw_sql import RawSQL


class TestCaseRunStatusTestCase(unittest.TestCase):
    # Number of testruns to use as sample during testing
    SAMPLE_SIZE = 1000

    def setUp(self):
        print 'Preparing testruns for testing testcaseruns statistics ' \
              'calculation ...'
        testruns_count = models.TestRun.objects.count()
        sample_run_ids = random.sample(range(1, testruns_count),
                                       self.SAMPLE_SIZE)
        testruns = models.TestRun.objects.filter(pk__in=sample_run_ids)
        # prepare data using OLD SQL-based query
        testruns = testruns.extra(
            select={
                'total_num_caseruns_by_sql':
                    RawSQL.total_num_caseruns,
                'completed_case_run_percent_by_sql':
                    RawSQL.completed_case_run_percent,
                'failed_case_run_percent_by_sql':
                    RawSQL.failed_case_run_percent,
                'passed_case_run_percent_by_sql':
                    RawSQL.passed_case_run_percent,
            }
        )
        self.sample_runs = testruns
        # To store TestCaseRuns that have been changed during the test,
        # so that in tearDown(), they could be restored.
        self.modified_caseruns = {}
        print 'Testruns prepared'

    def compareValues(self):
        print 'Comparing statistics'
        for run in self.sample_runs:
            self.assertEqual(
                run.total_num_caseruns_by_sql,
                run.total_num_caseruns
            )
            self.assertEqual(
                run.completed_case_run_percent_by_sql,
                run.completed_case_run_percent
            )
            self.assertEqual(
                run.failed_case_run_percent_by_sql,
                run.failed_case_run_percent
            )
            self.assertEqual(
                run.passed_case_run_percent_by_sql,
                run.passed_case_run_percent
            )
        print 'Done comparing'

    def testStatusChange(self):
        self.compareValues()
        print 'Randomly update caserunstatus and then compare statistics again'
        statuses = models.TestCaseRunStatus.objects.all()

        def get_a_different_status(original_status):
            new_status = None
            while True:
                status = random.choice(statuses)
                if status != original_status:
                    new_status = status
                    break
            return new_status

        for run in self.sample_runs:
            caseruns = run.case_run.all()
            for caserun in caseruns:
                # update caserunstatus randomly
                original_status = caserun.case_run_status
                self.modified_caseruns[caserun.pk] = original_status
                new_status = get_a_different_status(original_status)
                caserun.case_run_status = new_status
                caserun.save()
        self.compareValues()

    def tearDown(self):
        print 'Restoring changes made on caseruns'
        for caserun_pk, status in self.modified_caseruns.iteritems():
            caserun = models.TestCaseRun.objects.get(pk=caserun_pk)
            caserun.case_run_status = status
            caserun.save()
        print 'Done restoring TestCaseRun that have been modified'


if __name__ == '__main__':
    unittest.main()
