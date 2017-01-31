# -*- coding: utf-8 -*-
from collections import namedtuple
from itertools import groupby

from django.conf import settings
from django.db.models import Count, F
from django.contrib.contenttypes.models import ContentType
from django_comments.models import Comment

from tcms.testcases.models import TestCaseBug
from tcms.testruns.models import TestCaseRun
from tcms.testruns.models import TestCaseRunStatus


TestCaseRunStatusSubtotal = namedtuple('TestCaseRunStatusSubtotal',
                                       'StatusSubtotal '
                                       'CaseRunsTotalCount '
                                       'CompletedPercentage '
                                       'FailurePercentage')


def stats_caseruns_status(run_id, case_run_statuss):
    """Get statistics based on case runs' status

    @param run_id: id of test run from where to get statistics
    @type run_id: int
    @param case_run_statuss: iterable object containing TestCaseRunStatus
        objects representing PASS, FAIL, WAIVED, etc.
    @type case_run_statuss: iterable object
    @return: the statistics including the number of each status mapping,
        total number of case runs, complete percent, and failure percent.
    @rtype: namedtuple
    """
    rows = TestCaseRun.objects.filter(
        run=run_id
    ).values(
        'case_run_status'
    ).annotate(status_count=Count('case_run_status'))

    caserun_statuss_subtotal = dict((status.pk, [0, status])
                                    for status in case_run_statuss)

    for row in rows:
        status_pk = row['case_run_status']
        caserun_statuss_subtotal[status_pk][0] = row['status_count']

    complete_count = 0
    failure_count = 0
    caseruns_total_count = 0
    status_complete_names = TestCaseRunStatus.complete_status_names
    status_failure_names = TestCaseRunStatus.failure_status_names

    for status_pk, total_info in caserun_statuss_subtotal.iteritems():
        status_caseruns_count, caserun_status = total_info
        status_name = caserun_status.name

        caseruns_total_count += status_caseruns_count

        if status_name in status_complete_names:
            complete_count += status_caseruns_count
        if status_name in status_failure_names:
            failure_count += status_caseruns_count

    # Final calculation
    complete_percent = .0
    if caseruns_total_count:
        complete_percent = complete_count * 100.0 / caseruns_total_count
    failure_percent = .0
    if complete_count:
        failure_percent = failure_count * 100.0 / complete_count

    return TestCaseRunStatusSubtotal(caserun_statuss_subtotal,
                                     caseruns_total_count,
                                     complete_percent,
                                     failure_percent)


def get_run_bug_ids(run_id):
    """Get list of pairs of bug ID and bug link that are added to a run

    :param int run_id: ID of test run.
    :return: list of pairs of bug ID and bug link.
    :rtype: list
    """
    rows = TestCaseBug.objects.values(
        'bug_id',
        'bug_system__url_reg_exp'
    ).distinct().filter(case_run__run=run_id)

    return [(row['bug_id'], row['bug_system__url_reg_exp'] % row['bug_id'])
            for row in rows]


class TestCaseRunDataMixin(object):
    '''Data for test case runs'''

    def stats_mode_caseruns(self, case_runs):
        '''Statistics from case runs mode

        @param case_runs: iteratable object to access each case run
        @type case_runs: iterable, list, tuple
        @return: mapping between mode and the count. Example return value is
            { 'manual': I, 'automated': J, 'manual_automated': N }
        @rtype: dict
        '''
        manual_count = 0
        automated_count = 0
        manual_automated_count = 0

        for case_run in case_runs:
            is_automated = case_run.case.is_automated
            if is_automated == 1:
                automated_count += 1
            elif is_automated == 0:
                manual_count += 1
            else:
                manual_automated_count += 1

        return {
            'manual': manual_count,
            'automated': automated_count,
            'manual_automated': manual_automated_count,
        }

    def get_caseruns_bugs(self, run_pk):
        """Get case run bugs for run report

        :param int run_pk: run's pk whose case runs' bugs will be retrieved.
        :return: the mapping between case run id and bug information containing
            formatted bug URL.
        :rtype: dict
        """
        rows = []
        bugs = TestCaseBug.objects \
            .filter(case_run__run=run_pk) \
            .values('case_run', 'bug_id', 'bug_system__url_reg_exp') \
            .order_by('case_run')
        for row in bugs:
            row['bug_url'] = row['bug_system__url_reg_exp'] % row['bug_id']
            rows.append(row)
        return dict([(case_run_id, list(bugs_info)) for case_run_id, bugs_info in
                     groupby(rows, lambda row: row['case_run'])])

    def get_caseruns_comments(self, run_pk):
        '''Get case runs' comments

        @param run_pk: run's pk whose comments will be retrieved.
        @type run_pk: int
        @return: the mapping between case run id and comments
        @rtype: dict
        '''
        ct = ContentType.objects.get_for_model(TestCaseRun)

        rows = []
        for row in Comment.objects.filter(
                site=settings.SITE_ID,
                content_type=ct.pk,
                is_public=True,
                is_removed=False,
                object_pk__in=TestCaseRun.objects.filter(
                    run=run_pk)).annotate(
                case_run_id=F('object_pk')).values(
                'case_run_id',
                'submit_date',
                'comment').order_by('case_run_id'):
            rows.append(row)

        return dict([(key, list(groups)) for key, groups in
                     groupby(rows, lambda row: row['case_run_id'])])

    def get_summary_stats(self, case_runs):
        '''Get summary statistics from case runs

        Statistics targets:
        - the number of pending test case runs, whose status is IDLE
        - the number of completed test case runs, whose status are PASSED,
          ERROR, FAILED, WAIVED

        @param case_runs: iterable object containing case runs
        @type case_runs: iterable
        @return: a mapping between statistics target and its value
        @rtype: dict
        '''
        idle_count = 0
        complete_count = 0
        complete_status_names = TestCaseRunStatus.complete_status_names
        idle_status_names = TestCaseRunStatus.idle_status_names

        for case_run in case_runs:
            status_name = case_run.case_run_status.name
            if status_name in idle_status_names:
                idle_count += 1
            elif status_name in complete_status_names:
                complete_count += 1

        return {'idle': idle_count, 'complete': complete_count}
