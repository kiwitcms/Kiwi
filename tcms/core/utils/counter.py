# -*- coding: utf-8 -*-
from tcms.testruns.models import TestCaseRunStatus


class CaseRunStatusCounter:
    """
    The class is use for handle count the case run with status.
    Escape the heavy work for database
    """

    def __init__(self, case_runs):
        self.case_run_status = []
        self.count_data = {}
        # self.case_runs = case_runs.select_related('case_run_status')
        self.case_runs = case_runs.select_related(
            'case_run_status')

        for tcrs in TestCaseRunStatus.objects.all():
            self.count_data[tcrs] = 0
            self.case_run_status.append(tcrs)
        self.total = len(self.case_runs)
        self.count()

    def count(self):
        """
        Count the case run numbers by case run status
        """
        for case_run in self.case_runs:
            if case_run.case_run_status in self.case_run_status:
                self.count_data[case_run.case_run_status] += 1

        return self

    def complete_percent(self):
        """
        Calculate the complete percent
        """
        if not self.total:
            return 0
        percent = 0.0
        for case_run in self.case_run_status:
            if case_run.name in ['PASSED', 'ERROR', 'FAILED', 'WAIVED']:
                percent += self.count_data[case_run]
        return percent / self.total * 100

    def failed_percent(self):
        """
        Calculate the failed percent
        """
        if not self.total:
            return 0
        c_percent = 0.0
        f_percent = 0.0
        for case_run in self.case_run_status:
            if case_run.name in ['PASSED', 'ERROR', 'FAILED', 'WAIVED']:
                c_percent += self.count_data[case_run]
            if case_run.name in ['ERROR', 'FAILED']:
                f_percent += self.count_data[case_run]
        return (c_percent > 0) and f_percent / c_percent * 100 or 0.0


class RunsCounter:
    def __init__(self, running=0, finished=0):
        self.running = running
        self.finished = finished
        self.total = running + finished

    def running_percent(self):
        try:
            return float(self.running) / self.total * 100
        except:
            return 0

    def finished_percent(self):
        try:
            return float(self.finished) / self.total * 100
        except:
            return 0

# Self testing code
if __name__ == '__main__':
    from tcms.testcases.models import TestCaseRun
    from pprint import pprint

    tcrs = TestCaseRun.objects.filter(run__run_id=33)
    case_run_counter = CaseRunStatusCounter(tcrs)
    pprint(case_run_counter.__dict__)
