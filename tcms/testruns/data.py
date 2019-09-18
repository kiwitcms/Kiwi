# -*- coding: utf-8 -*-

from itertools import groupby

from django.conf import settings
from django.db.models import F
from django.contrib.contenttypes.models import ContentType
from django_comments.models import Comment

from tcms.testruns.models import TestExecution
from tcms.testruns.models import TestExecutionStatus


class TestExecutionDataMixin:
    """Data for test executions"""

    @staticmethod
    def stats_mode_executions(executions):
        """
            Statistics from executions mode

            :param executions: iteratable object to access each execution
            :type executions: iterable, list, tuple
            :return: mapping between mode and the count. Example return value is
                     `{ 'manual': I, 'automated': J }`
            :rtype: dict
        """
        manual_count = 0
        automated_count = 0

        for execution in executions:
            if execution.case.is_automated:
                automated_count += 1
            else:
                manual_count += 1

        return {
            'manual': manual_count,
            'automated': automated_count,
        }

    @staticmethod
    def get_execution_comments(run_pk):
        """Get executions' comments

        :param run_pk: run's pk whose comments will be retrieved.
        :type run_pk: int
        :return: the mapping between execution id and comments
        :rtype: dict
        """
        # note: cast to string b/c object_pk is a Textield and PostgreSQL
        # doesn't like TEXT in <list of integers>
        # in Django 1.10 we have the Cast() function for similar cases, see
        # https://docs.djangoproject.com/en/1.10/ref/models/database-functions/#cast
        object_pks = []
        for execution in TestExecution.objects.filter(run=run_pk).only('pk'):
            object_pks.append(str(execution.pk))

        comments = Comment.objects.filter(
            site=settings.SITE_ID,
            content_type=ContentType.objects.get_for_model(TestExecution).pk,
            is_public=True,
            is_removed=False,
            object_pk__in=object_pks
        ).annotate(
            case_run_id=F('object_pk')
        ).values(
            'case_run_id',
            'submit_date',
            'comment',
            'user_name'
        ).order_by('case_run_id')

        rows = []
        for row in comments:
            rows.append(row)

        case_run_comments = {}
        for key, groups in groupby(rows, lambda row: row['case_run_id']):
            case_run_comments[int(key)] = list(groups)

        return case_run_comments

    @staticmethod
    def get_summary_stats(executions):
        """Get summary statistics from executions

        Statistics targets:

        - the number of pending test executionss, whose status is IDLE
        - the number of completed test executionss, whose status are PASSED,
          ERROR, FAILED, WAIVED

        :param executions: iterable object containing executionss
        :type executions: iterable
        :return: a mapping between statistics target and its value
        :rtype: dict
        """
        idle_count = 0
        complete_count = 0
        for case_run in executions:
            if case_run.status.name in TestExecutionStatus.idle_status_names:
                idle_count += 1
            elif case_run.status.name in TestExecutionStatus.complete_status_names:
                complete_count += 1

        return {'idle': idle_count, 'complete': complete_count}
