# -*- coding: utf-8 -*-
from collections import defaultdict
from collections import namedtuple
from itertools import chain
from itertools import groupby
from itertools import imap

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.db.models import Count

from tcms.management.models import Priority
from tcms.testcases.models import TestCaseBug
from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestCaseRun
from tcms.testruns.models import TestCaseRunStatus
from tcms.testruns.models import TestRun
from tcms.core.db import get_groupby_result
from tcms.core.db import SQLExecution
from tcms.core.db import GroupByResult
from tcms.core.db import workaround_single_value_for_in_clause
from tcms.report import sqls
from tcms.management.models import TestBuild


__all__ = (
    'CustomDetailsReportData',
    'CustomReportData',
    'ProductBuildReportData',
    'ProductComponentReportData',
    'ProductVersionReportData',
    'TestingReportByCasePriorityData',
    'TestingReportByCaseRunTesterData',
    'TestingReportByPlanBuildData',
    'TestingReportByPlanTagsData',
    'TestingReportByPlanTagsDetailData',
    'TestingReportCaseRunsData',
)


def models_to_pks(models):
    return workaround_single_value_for_in_clause(
        [model.pk for model in models])


def model_to_pk(model):
    return model.pk


def do_nothing(value):
    return value


class ProductBuildReportData(object):
    '''Report data by builds of a Product'''

    def total_runs_count(self, product_id):
        return get_groupby_result(sqls.build_builds_total_runs_count,
                                  (product_id,),
                                  key_name='build_id')

    def finished_runs_count(self, product_id):
        return get_groupby_result(sqls.build_builds_finished_runs_count,
                                  (product_id,),
                                  key_name='build_id')

    def finished_caseruns_count(self, product_id):
        return get_groupby_result(sqls.build_finished_caseruns_count,
                                  (product_id,),
                                  key_name='build_id')

    def failed_caseruns_count(self, product_id):
        return get_groupby_result(sqls.build_failed_caseruns_count,
                                  (product_id,),
                                  key_name='build_id')

    def caseruns_count(self, product_id):
        return get_groupby_result(sqls.build_caseruns_count,
                                  (product_id,),
                                  key_name='build_id')

    def caserun_status_subtotal(self, product_id, build_id):
        return get_groupby_result(sqls.build_caserun_status_subtotal,
                                  (product_id, build_id),
                                  key_name='name',
                                  with_rollup=True)


class ProductComponentReportData(object):
    def total_cases(self, product_id):
        return get_groupby_result(sqls.component_total_cases,
                                  (product_id,),
                                  key_name='component_id')

    def failed_case_runs_count(self, product_id):
        return get_groupby_result(sqls.component_failed_case_runs_count,
                                  (product_id,),
                                  key_name='component_id')

    def finished_case_runs_count(self, product_id):
        return get_groupby_result(sqls.component_finished_case_runs_count,
                                  (product_id,),
                                  key_name='component_id')

    def total_case_runs_count(self, product_id):
        return get_groupby_result(sqls.component_total_case_runs_count,
                                  (product_id,),
                                  key_name='component_id')

    def case_runs_count(self, component_id):
        return get_groupby_result(sqls.component_case_runs_count,
                                  (component_id,),
                                  key_name='name',
                                  with_rollup=True)


class ProductVersionReportData(object):
    '''Report data by versions of a Product'''

    def plans_subtotal(self, product_id):
        return get_groupby_result(sqls.version_plans_subtotal,
                                  (product_id,),
                                  key_name='product_version_id')

    def running_runs_subtotal(self, product_id):
        return get_groupby_result(sqls.version_running_runs_subtotal,
                                  (product_id,),
                                  key_name='product_version_id')

    def finished_runs_subtotal(self, product_id):
        return get_groupby_result(sqls.version_finished_runs_subtotal,
                                  (product_id,),
                                  key_name='product_version_id')

    def cases_subtotal(self, product_id):
        return get_groupby_result(sqls.version_cases_subtotal,
                                  (product_id,),
                                  key_name='product_version_id')

    def case_runs_subtotal(self, product_id):
        return get_groupby_result(sqls.version_case_runs_subtotal,
                                  (product_id,),
                                  key_name='product_version_id')

    def finished_case_runs_subtotal(self, product_id):
        return get_groupby_result(sqls.version_finished_case_runs_subtotal,
                                  (product_id,),
                                  key_name='product_version_id')

    def failed_case_runs_subtotal(self, product_id):
        return get_groupby_result(sqls.version_failed_case_runs_subtotal,
                                  (product_id,),
                                  key_name='product_version_id')

    def case_runs_status_subtotal(self, product_id, version_id):
        subtotal = {}
        total = 0
        for row in TestCaseRun.objects.filter(
                run__plan__product=product_id,
                run__plan__product_version=version_id
            ).values('case_run_status__name').annotate(
                status_count=Count('case_run_status__name'
            )):
            subtotal[row['case_run_status__name']] = row['status_count']
            total += row['status_count']
        subtotal['TOTAL'] = total
        return subtotal


SQLQueryInfo = namedtuple('SQLQueryInfo',
                          'joins, where_condition, where_param_conv')


class CustomReportData(object):
    '''Data for custom report

    In this data class, a major task is to construct INNER JOINS dynamically
    according to criteria selected by user.

    INNER JOINS include must-exist joins for getting data, and other potential
    ones that should be added according to criteria user specifies.

    One important thing is to ensure final INNER JOINS should be unique, so
    that no unnecessary table-join operation happens in database.
    '''

    # All data are selected FROM test_builds, so following INNER JOINS are
    # relative to test_builds.
    # No wired to duplicated INNER JOINS in the following definition for each
    # criteria, it'll ensure that they are unique in final SQL statement.
    report_criteria = {
        'pk__in': SQLQueryInfo(None,
                               'test_builds.build_id IN %s', models_to_pks),

        'product': SQLQueryInfo(None,
                                'test_builds.product_id = %s', model_to_pk),

        'build_run__product_version': SQLQueryInfo(
            ('INNER JOIN test_runs ON '
             '(test_builds.build_id = test_runs.build_id)',),
            'test_runs.product_version_id = %s', model_to_pk),

        'build_run__plan__name__icontains': SQLQueryInfo(
            ('INNER JOIN test_runs ON '
             '(test_builds.build_id = test_runs.build_id)',
             'INNER JOIN test_plans ON '
             '(test_runs.plan_id = test_plans.plan_id)'),
            'test_plans.name LIKE %%%s%%', do_nothing),

        'testcaserun__case__category': SQLQueryInfo(
            ('INNER JOIN test_runs ON '
             '(test_builds.build_id = test_runs.build_id)',
             'INNER JOIN test_case_runs ON '
             '(test_runs.run_id = test_case_runs.run_id)',
             'INNER JOIN test_cases ON '
             '(test_case_runs.case_id = test_cases.case_id)'),
            'test_cases.category_id = %s', model_to_pk),

        'testcaserun__case__component': SQLQueryInfo(
            ('INNER JOIN test_runs ON '
             '(test_builds.build_id = test_runs.build_id)',
             'INNER JOIN test_case_runs ON '
             '(test_runs.run_id = test_case_runs.run_id)',
             'INNER JOIN test_cases ON '
             '(test_case_runs.case_id = test_cases.case_id)',
             'INNER JOIN test_case_components '
             'ON (test_cases.case_id = test_case_components.case_id)'),
            'test_case_components.component_id = %s', model_to_pk),
    }

    def __init__(self, form):
        self._form = form

    def _filter_criteria(self):
        '''Singleton method ensures criteria are constructed only once

        @return: a tuple containing joins, where conditions, and where params
        @rtype: tuple
        '''
        filter_criteria = getattr(self, '__filter_criteria', None)
        if filter_criteria is None:
            joins = []
            where_conditions = []
            where_params = []
            for field_name, value in self._form.cleaned_data.iteritems():
                if not value:
                    continue
                query_info = self.report_criteria[field_name]
                if query_info.joins:
                    for item in query_info.joins:
                        if item not in joins:
                            joins.append(item)
                if query_info.where_condition:
                    where_conditions.append(query_info.where_condition)
                where_params.append(query_info.where_param_conv(value))
            filter_criteria = (joins, where_conditions, where_params)
            self.__filter_criteria = filter_criteria
        return filter_criteria

    def _prepare_sql(self, sql_statement):
        '''Prepare SQL statement by constructing JOINS and WHERE clause'''

        joins, where_conditions, where_params = self._filter_criteria()

        # Chain JOINs
        _joins = list(sql_statement.default_joins)
        for item in joins:
            # To avoid duplicated JOIN, whatever INNER JOIN or LEFT JOIN
            # Duplicated JOIN would cause database level error.
            if item not in _joins:
                _joins.append(item)

        _where_conditions = chain(sql_statement.default_where,
                                  where_conditions)

        sql = sql_statement.sql_template % {
            'joins': '\n'.join(_joins),
            'where': ' AND '.join(imap(str, _where_conditions)),
        }
        return sql, where_params

    # especially when filter builds with component.
    def _get_builds(self):
        '''Get builds from valid form

        @param form: the form containing valid data
        @type form: L{CustomSearchForm}
        @return: queried test builds
        @rtype: L{QuerySet}
        '''
        sql, params = self._prepare_sql(sqls.custom_builds)
        rows = SQLExecution(sql, params).rows
        return [TestBuild(pk=row['build_id'], name=row['name'])
                for row in rows]

    # ## Summary header data ###

    def runs_subtotal(self):
        sql, params = self._prepare_sql(sqls.custom_builds_runs_subtotal)
        return get_groupby_result(sql, params,
                                  key_name='build_id',
                                  with_rollup=True)

    def plans_subtotal(self):
        sql, params = self._prepare_sql(sqls.custom_builds_plans_subtotal)
        return get_groupby_result(sql, params,
                                  key_name='build_id',
                                  with_rollup=True)

    def case_runs_subtotal(self):
        sql, params = self._prepare_sql(sqls.custom_builds_case_runs_subtotal)
        return get_groupby_result(sql, params, key_name='build_id')

    def cases_isautomated_subtotal(self):
        sql, params = self._prepare_sql(
            sqls.custom_builds_cases_isautomated_subtotal)
        return get_groupby_result(sql, params,
                                  key_name='isautomated',
                                  with_rollup=True)

    # ## Case run status matrix to show progress bar for each build ###

    def status_matrix(self):
        '''Case run status matrix used to render progress bar'''
        sql, params = self._prepare_sql(
            sqls.custom_builds_case_runs_subtotal_by_status)
        rows = SQLExecution(sql, params, with_field_name=False).rows

        builds = GroupByResult()
        for build_id, case_run_status_id, total_count in rows:
            status_subtotal = builds.setdefault(build_id, GroupByResult())
            status_subtotal[case_run_status_id] = total_count

        return builds


class CustomDetailsReportData(CustomReportData):
    '''Data for custom details report

    Inherits from CustomReportData is becuase details report also need the
    summary header data and the progress bar for being viewed test build. You
    may treat the latter one as a subset of custom report.

    Besides above same data, details report also defines following methods to
    get specific data for detailed information to show to user.
    '''

    # In detail report, there is only one selected test build at a time.
    report_criteria = CustomReportData.report_criteria.copy()
    report_criteria['pk__in'] = SQLQueryInfo(None,
                                             'test_builds.build_id = %s',
                                             model_to_pk)

    def _get_builds(self):
        builds = TestBuild.objects.filter(
            pk=self._form.cleaned_data['pk__in'].pk,
            product=self._form.cleaned_data['product'])
        return builds.select_related('product').only('product__id', 'name')

    def generate_status_matrix(self, build_ids):
        matrix_dataset = {}
        # TODO: replace defaultdict with GroupByResult
        status_total_line = defaultdict(int)

        rows = SQLExecution(sqls.custom_details_status_matrix,
                            params=(build_ids,),
                            with_field_name=False).rows

        for row in rows:
            plan_id, plan_name, run_id, run_summary, \
                status_name, status_count = row
            plan = TestPlan(pk=plan_id, name=plan_name)
            plan_node = matrix_dataset.setdefault(plan, {})

            run = TestRun(pk=run_id, summary=run_summary)
            run_node = plan_node.setdefault(run, defaultdict(int))

            run_node[status_name] = status_count
            run_node['TOTAL'] += status_count

            # calculate the last total line
            status_total_line[status_name] += status_count
            status_total_line['TOTAL'] += status_count

        # Add total line to final data set
        matrix_dataset[None] = status_total_line
        return matrix_dataset

    def get_case_runs(self, build_ids, status_ids):
        '''Get case runs according to builds and status

        @param build_ids: IDs of builds
        @type build_ids: list or tuple
        @param status_ids: IDs of case run status
        @type status_ids: list or tuple
        @return: queried case runs
        @rtype: L{QuerySet}
        '''
        tcrs = TestCaseRun.objects.filter(run__build__in=build_ids,
                                          case_run_status_id__in=status_ids)
        tcrs = tcrs.select_related('run', 'case',
                                   'case__category',
                                   'tested_by')
        tcrs = tcrs.only('run', 'case__summary', 'case__category__name',
                         'tested_by__username', 'close_date')
        tcrs = tcrs.order_by('case')
        return tcrs

    def get_case_runs_bugs(self, build_ids, status_ids):
        '''Get case runs' bugs according to builds and status

        @param build_ids: IDs of builds
        @type build_ids: list or tuple
        @param status_ids: IDs of case run status
        @type status_ids: list or tuple
        @return: mapping between case run ID and its bugs
        @rtype: dict
        '''
        bugs = TestCaseBug.objects.filter(
            case_run__run__build__in=build_ids,
            case_run__case_run_status_id__in=status_ids)
        bugs = bugs.select_related('bug_system')
        bugs = bugs.only('bug_id',
                         'bug_system__url_reg_exp',
                         'case_run')
        return dict((case_run_id, list(bugs)) for case_run_id, bugs in
                    groupby(bugs, key=lambda bug: bug.case_run_id))

    def get_case_runs_comments(self, build_ids, status_ids):
        '''Get case runs' bugs according to builds and status

        @param build_ids: IDs of builds
        @type build_ids: list or tuple
        @param status_ids: IDs of case run status
        @type status_ids: list or tuple
        @return: mapping between case run ID and its comments
        @rtype: dict
        '''
        ct = ContentType.objects.get_for_model(TestCaseRun)
        rows = SQLExecution(sqls.custom_details_case_runs_comments,
                            (ct.pk, build_ids, status_ids)).rows
        return dict((case_run_id, list(comments)) for case_run_id, comments in
                    groupby(rows, key=lambda row: row['case_run_id']))


class TestingReportBaseData(object):
    '''Base data of various testing report'''

    report_criteria = {
        'r_product': ('test_builds.product_id = %s', lambda obj: obj.pk),
        'r_build': ('test_runs.build_id IN %s', models_to_pks),
        'r_created_since': ('test_runs.start_date >= %s', do_nothing),
        'r_created_before': ('test_runs.start_date <= %s', do_nothing),
        'r_version': ('test_runs.product_version_id IN %s', models_to_pks),
    }

    # ## Helper methods ###

    def get_build_names(self, build_ids):
        return dict(TestBuild.objects.filter(
            pk__in=build_ids).values_list('pk', 'name').iterator())

    def get_usernames(self, user_ids):
        return dict(User.objects.filter(
            id__in=user_ids).values_list('id', 'username').iterator())

    # ## SQL preparation ###

    def _report_criteria(self, form):
        '''cache criteria to avoid generating repeately'''
        where_clause = []
        params = []
        for field, condition in self.report_criteria.iteritems():
            param = form.cleaned_data[field]
            if param:
                expr, value_conv = condition
                where_clause.append(expr)
                params.append(value_conv(param))
        return ' AND '.join(where_clause), params

    def _prepare_sql(self, form, sql):
        where_clause, params = self._report_criteria(form)
        return sql.format(where_clause), params

    # ## Report data generation ###

    def _get_report_data(self, form, builds, builds_selected):
        '''
        The core method to generate report data. Remain for subclass to
        implement

        @param form: the valid form containing report criteria
        @type form: L{RunForm}
        @param builds: sequence of TestBuilds, either selected by user or the
            all builds of selected product
        @type builds: list or tuple
        @param builds_select: whether the builds are selected by user
        @type builds_selected: bool
        @return: the report data
        @rtype: dict
        '''
        raise NotImplementedError

    def _get_builds(self, form):
        '''Get selected or all product's builds for display'''
        builds = form.cleaned_data['r_build']
        builds_selected = len(builds) > 0
        if len(builds) == 0:
            product = form.cleaned_data['r_product']
            builds = TestBuild.objects.filter(product=product).only('name')
        return builds, builds_selected

    def get_report_data(self, form):
        '''Core method to get report data exported to testing report view'''
        builds, builds_selected = self._get_builds(form)
        data = self._get_report_data(form, builds, builds_selected)
        data.update({
            'builds_selected': builds_selected,
            'builds': builds,
        })
        return data

    # ## Shared report data ###

    def plans_count(self, form):
        sql, params = self._prepare_sql(form, sqls.testing_report_plans_total)
        sql_executor = SQLExecution(sql, params)
        return sql_executor.scalar

    def runs_count(self, form):
        sql, params = self._prepare_sql(form,
                                        sqls.testing_report_runs_total)
        sql_executor = SQLExecution(sql, params)
        return sql_executor.scalar


class TestingReportByCaseRunTesterData(TestingReportBaseData):
    '''Data for testing report of By Case Run Tester'''

    def _get_report_data(self, form, builds, builds_selected):
        if builds_selected:
            return self._get_report_data_with_builds(form, builds)
        else:
            return self._get_report_data_without_builds_selected(form)

    def _get_report_data_without_builds_selected(self, form):
        '''Get report data when user does not select any build'''
        plans_count = self.plans_count(form)
        runs_count = self.runs_count(form)
        status_matrix = self.status_matrix(form)
        runs_subtotal = self.runs_subtotal(form)

        tested_by_usernames = self.get_usernames(status_matrix.keys())

        def walk_status_matrix_rows():
            tested_by_ids = sorted(status_matrix.iteritems(),
                                   key=lambda item: item[0])
            for tested_by_id, status_subtotal in tested_by_ids:
                tested_by_username = tested_by_usernames.get(tested_by_id,
                                                             'None')
                tested_by = None
                if tested_by_username is not None:
                    tested_by = User(pk=tested_by_id,
                                     username=tested_by_username)
                runs_count = runs_subtotal.get(tested_by_id, 0)
                yield tested_by, runs_count, status_subtotal

        return {
            'plans_count': plans_count,
            'runs_count': runs_count,
            'caseruns_count': status_matrix.total,
            'reports': walk_status_matrix_rows(),
        }

    def _get_report_data_with_builds(self, form, builds):
        '''Get report data when user selects one or more builds

        @param form: the valid form containing report criteria
        @type form: L{RunForm}
        @param builds: selected builds by user
        @type builds: list
        @return: report data containing all necessary data grouped by selected
            builds and tested_bys
        @rtype: dict
        '''
        plans_count = self.plans_count(form)
        runs_count = self.runs_count(form)
        status_matrix = self.status_matrix_groupby_builds(form)
        runs_subtotal = self.runs_subtotal_groupby_builds(form)

        # Get related tested_by's username. Don't need duplicated user ids.
        tested_by_ids = []
        for build_id, tested_bys in status_matrix.iteritems():
            tested_by_ids += tested_bys.keys()
        tested_by_ids = set(tested_by_ids)

        build_names = self.get_build_names(build.pk for build in builds)
        tested_by_names = self.get_usernames(tested_by_ids)

        def walk_status_matrix_rows():
            '''For rendering template, walk through status matrix row by row'''
            prev_build = None
            builds = sorted(status_matrix.iteritems(),
                            key=lambda item: item[0])
            for build_id, tested_by_ids in builds:
                build_rowspan = len(tested_by_ids)
                tested_by_ids = sorted(tested_by_ids.iteritems(),
                                       key=lambda item: item[0])
                for tested_by_id, status_subtotal in tested_by_ids:
                    if build_id not in runs_subtotal:
                        runs_count = 0
                    elif tested_by_id not in runs_subtotal[build_id]:
                        runs_count = 0
                    else:
                        runs_count = runs_subtotal[build_id][tested_by_id]

                    build = TestBuild(pk=build_id,
                                      name=build_names.get(build_id, ''))
                    if build == prev_build:
                        _build = (build, None)
                    else:
                        _build = (build, build_rowspan)
                        prev_build = build

                    tested_by_username = tested_by_names.get(tested_by_id,
                                                             None)
                    tested_by = None
                    if tested_by_username is not None:
                        tested_by = User(pk=tested_by_id,
                                         username=tested_by_username)

                    yield _build, tested_by, runs_count, status_subtotal

        return {
            'plans_count': plans_count,
            'runs_count': runs_count,
            'caseruns_count': status_matrix.total,
            'reports': walk_status_matrix_rows(),
        }

    def status_matrix(self, form):
        sql, params = self._prepare_sql(
            form, sqls.by_case_run_tester_status_matrix)
        sql_executor = SQLExecution(sql, params,
                                    with_field_name=False)
        status_matrix = GroupByResult({})
        rows = sql_executor.rows

        for tested_by_id, name, total_count in rows:
            status_subtotal = status_matrix.setdefault(
                tested_by_id, GroupByResult({}))
            status_subtotal[name] = total_count

        return status_matrix

    def runs_subtotal(self, form):
        sql, params = self._prepare_sql(
            form, sqls.by_case_run_tester_runs_subtotal)
        return get_groupby_result(sql, params,
                                  key_name='tested_by_id')

    def status_matrix_groupby_builds(self, form):
        sql, params = self._prepare_sql(
            form, sqls.by_case_run_tester_status_matrix_groupby_build)
        sql_executor = SQLExecution(sql, params,
                                    with_field_name=False)

        builds = GroupByResult({})

        for build_id, tested_by_id, name, total_count in sql_executor.rows:
            tested_by_ids = builds.setdefault(
                build_id, GroupByResult({}))
            status_subtotal = tested_by_ids.setdefault(tested_by_id,
                                                       GroupByResult({}))
            status_subtotal[name] = total_count

        return builds

    def runs_subtotal_groupby_builds(self, form):
        sql, params = self._prepare_sql(
            form, sqls.by_case_run_tester_runs_subtotal_groupby_build)
        sql_executor = SQLExecution(sql, params,
                                    with_field_name=False)
        rows = sql_executor.rows

        builds = GroupByResult({})

        for build_id, tested_by_id, total_count in rows:
            tested_by_ids = builds.setdefault(build_id, GroupByResult({}))
            tested_by_ids[tested_by_id] = total_count

        return builds


class TestingReportByCasePriorityData(TestingReportBaseData):
    '''Data for testing report By Case Priority'''

    def _get_report_data(self, form, builds, builds_selected):
        plans_count = self.plans_count(form)
        runs_count = self.runs_subtotal(form).total
        status_matrix = self.status_matrix(form)

        build_ids = status_matrix.keys()
        builds_names = self.get_build_names(build_ids)

        def walk_status_matrix_rows():
            prev_build_id = None
            ordered_builds = sorted(status_matrix.iteritems(),
                                    key=lambda item: item[0])
            for build_id, priorities in ordered_builds:
                build_rowspan = len(priorities)
                ordered_priorities = sorted(priorities.iteritems(),
                                            key=lambda item: item[0].value)
                build_name = builds_names.get(build_id, '')
                for priority, status_subtotal in ordered_priorities:
                    if build_id == prev_build_id:
                        build = (build_id, build_name, None)
                    else:
                        build = (build_id, build_name, build_rowspan)
                        prev_build_id = build_id
                    yield build, priority, status_subtotal

        data = {
            'plans_count': plans_count,
            'runs_count': runs_count,
            'caseruns_count': status_matrix.total,
            'reports': walk_status_matrix_rows(),
        }
        return data

    def runs_subtotal(self, form):
        sql, params = self._prepare_sql(form,
                                        sqls.testing_report_runs_subtotal)
        return get_groupby_result(sql, params,
                                  key_name='build_id',
                                  with_rollup=True)

    def status_matrix(self, form):
        sql, params = self._prepare_sql(form, sqls.by_case_priority_subtotal)
        sql_executor = SQLExecution(sql, params, with_field_name=False)
        rows = sql_executor.rows

        builds = GroupByResult()

        for build_id, priority_id, priority_value, name, total_count in rows:
            priorities = builds.setdefault(build_id, GroupByResult())
            priority = Priority(pk=priority_id, value=priority_value)
            status_subtotal = priorities.setdefault(priority, GroupByResult())
            status_subtotal[name] = total_count

        return builds


class TestingReportByPlanTagsData(TestingReportBaseData):
    '''Data for testing report By Plan Tag'''

    def _get_report_data(self, form, builds, builds_selected):
        plans_count = self.plans_count(form)
        runs_count = self.runs_count(form)
        status_matrix = self.passed_failed_case_runs_subtotal(form)
        plans_subtotal = self.plans_subtotal(form)
        runs_subtotal = self.runs_subtotal(form)
        tags_names = self.get_tags_names(status_matrix.keys())

        def walk_status_matrix_rows():
            ordered_tags = sorted(status_matrix.iteritems(),
                                  key=lambda item: item[0])
            for tag_id, status_subtotal in ordered_tags:
                yield tags_names.get(tag_id, ''), \
                    plans_subtotal.get(tag_id, 0), \
                    runs_subtotal.get(tag_id, 0), \
                    status_subtotal

        return {
            'plans_count': plans_count,
            'runs_count': runs_count,
            'reports': walk_status_matrix_rows(),

            # This is only used for displaying tags in report
            'tags_names': [tags_names[key]
                           for key in sorted(tags_names.keys())],
        }

    def plans_subtotal(self, form):
        sql, params = self._prepare_sql(form,
                                        sqls.by_plan_tags_plans_subtotal)
        return get_groupby_result(sql, params, key_name='tag_id')

    def runs_subtotal(self, form):
        sql, params = self._prepare_sql(form,
                                        sqls.by_plan_tags_runs_subtotal)
        return get_groupby_result(sql, params, key_name='tag_id')

    def passed_failed_case_runs_subtotal(self, form):
        sql, params = self._prepare_sql(
            form, sqls.by_plan_tags_passed_failed_case_runs_subtotal)
        sql_executor = SQLExecution(sql, params, with_field_name=False)
        rows = sql_executor.rows
        tags = GroupByResult()

        for tag_id, name, total_count in rows:
            status_subtotal = tags.setdefault(tag_id, GroupByResult())
            status_subtotal[name] = total_count

        return tags

    def get_tags_names(self, tag_ids):
        '''Get tags names from status matrix'''
        from tcms.management.models import TestTag

        names = dict(TestTag.objects.filter(
            pk__in=tag_ids).values_list('pk', 'name').iterator())
        # The existence of None tells us the fact that there are plans without
        # any tag. So, name it untagged.
        if None in tag_ids:
            names[None] = 'untagged'
        return names


class TestingReportByPlanTagsDetailData(TestingReportByPlanTagsData):
    '''Detail data for testing report By Plan Tag'''

    def _get_report_data(self, form, builds, builds_selected):
        # Total section containing the number of plans, runs, and case runs
        # individually
        plans_count = self.plans_count(form)
        runs_count = self.runs_count(form)
        case_runs_count = self.case_runs_total(form)

        status_matrix = self.status_matrix(form)
        plans_subtotal = self.plans_subtotal(form)
        runs_subtotal = self.runs_subtotal(form)
        tags_names = self.get_tags_names(status_matrix.keys())

        def walk_status_matrix():
            status_matrix.leaf_values_count(value_in_row=True)
            ordered_builds = sorted(status_matrix.iteritems(),
                                    key=lambda item: item[0])
            for tag_id, builds in ordered_builds:
                # Data on top of each status matrix under each tag
                yield tags_names.get(tag_id, 'untagged'), \
                    plans_subtotal.get(tag_id, 0), \
                    runs_subtotal.get(tag_id, 0), \
                    builds.total, \
                    self.walk_status_matrix_rows(builds)

        return {
            'plans_count': plans_count,
            'runs_count': runs_count,
            'caseruns_count': case_runs_count,
            'reports': walk_status_matrix(),

            # This is only used for displaying tags in report
            'tags_names': (
                tags_names[key] for key in sorted(tags_names.keys())),
        }

    def walk_status_matrix_rows(self, root_matrix):
        '''Walk status matrix row by row'''
        def sort_key(item):
            return item[0].pk

        prev_build = None
        prev_plan = None

        ordered_builds = sorted(root_matrix.iteritems(), key=sort_key)
        for build, plans in ordered_builds:
            ordered_plans = sorted(plans.iteritems(), key=sort_key)
            build_rowspan = plans.leaf_values_count(value_in_row=True)
            for plan, runs in ordered_plans:
                ordered_runs = sorted(runs.iteritems(), key=sort_key)
                plan_rowspan = runs.leaf_values_count(value_in_row=True)
                for run, status_subtotal in ordered_runs:
                    if build == prev_build:
                        _build = (build, None)
                    else:
                        _build = (build, build_rowspan)
                        prev_build = build
                    # FIXME: find a better way, building a tuple seems not a
                    # good way, may cause performance issue
                    if (build, plan) == prev_plan:
                        _plan = (plan, None)
                    else:
                        _plan = (plan, plan_rowspan)
                        prev_plan = (build, plan)
                    yield _build, _plan, run, status_subtotal

    def status_matrix(self, form):
        sql, params = self._prepare_sql(form,
                                        sqls.by_plan_tags_detail_status_matrix)
        rows = SQLExecution(sql, params, with_field_name=False).rows

        status_matrix = GroupByResult()

        for row in rows:
            tag_id, build_id, build_name, plan_id, plan_name, run_id, \
                run_summary, status_name, total_count = row

            builds = status_matrix.setdefault(tag_id, GroupByResult())
            plans = builds.setdefault(TestBuild(pk=build_id, name=build_name),
                                      GroupByResult())
            runs = plans.setdefault(TestPlan(pk=plan_id, name=plan_name),
                                    GroupByResult())
            status_subtotal = runs.setdefault(
                TestRun(pk=run_id, summary=run_summary), GroupByResult())
            status_subtotal[status_name] = total_count

        return status_matrix

    def case_runs_total(self, form):
        sql, params = self._prepare_sql(form,
                                        sqls.testing_report_case_runs_total)
        return SQLExecution(sql, params).scalar


class TestingReportByPlanBuildData(TestingReportBaseData):
    '''Data of testing report By Plan Build'''

    def _get_report_data(self, form, builds, builds_selected):
        plans_count = self.plans_count(form)
        builds_subtotal = self.builds_subtotal(form)
        runs_subtotal = self.runs_subtotal(form)
        status_matrix = self.status_matrix(form)

        def walk_status_matrix_rows():
            ordered_plans = sorted(status_matrix.iteritems(),
                                   key=lambda item: item[0].pk)
            for plan, status_subtotal in ordered_plans:
                yield plan, \
                    builds_subtotal.get(plan, 0), \
                    runs_subtotal.get(plan, 0), \
                    status_matrix.get(plan, {})

        return {
            'plans_count': plans_count,
            'runs_count': runs_subtotal.total,
            'reports': walk_status_matrix_rows(),

            # only for displaying plan names
            'plans': (plan.name for plan, value in
                      sorted(status_matrix.iteritems(),
                             key=lambda item: item[0].pk))
        }

    def builds_subtotal(self, form):
        sql, params = self._prepare_sql(form,
                                        sqls.by_plan_build_builds_subtotal)
        rows = SQLExecution(sql, params, with_field_name=False).rows
        result = GroupByResult()
        for plan_id, plan_name, builds_count in rows:
            plan = TestPlan(pk=plan_id, name=plan_name)
            result[plan] = builds_count
        return result

    def runs_subtotal(self, form):
        sql, params = self._prepare_sql(form,
                                        sqls.by_plan_build_runs_subtotal)
        rows = SQLExecution(sql, params, with_field_name=False).rows
        result = GroupByResult()
        for plan_id, plan_name, runs_count in rows:
            plan = TestPlan(pk=plan_id, name=plan_name)
            result[plan] = runs_count
        return result

    def status_matrix(self, form):
        sql, params = self._prepare_sql(form,
                                        sqls.by_plan_build_status_matrix)
        rows = SQLExecution(sql, params, with_field_name=False).rows
        status_matrix = GroupByResult()
        for plan_id, plan_name, status_name, total_count in rows:
            plan = TestPlan(pk=plan_id, name=plan_name)
            status_subtotal = status_matrix.setdefault(plan, GroupByResult())
            status_subtotal[status_name] = total_count
        return status_matrix


class TestingReportByPlanBuildDetailData(TestingReportByPlanBuildData):
    '''Detail data of testing report By Plan Build Detail'''

    def _get_report_data(self, form, builds, builds_selected):
        plans_count = self.plans_count(form)
        builds_subtotal = self.builds_subtotal(form)
        runs_subtotal = self.runs_subtotal(form)
        status_matrix = self.status_matrix(form)

        case_runs_count = status_matrix.total
        # Force to calculate leaf values count to cache in each level
        status_matrix.leaf_values_count(value_in_row=True)

        def walk_status_matrix_rows():
            ordered_plans = sorted(status_matrix.iteritems(),
                                   key=lambda item: item[0].pk)
            for plan, builds in ordered_plans:
                builds_count = builds_subtotal.get(plan, 0)
                runs_count = runs_subtotal.get(plan, 0)
                caseruns_count = builds.total

                yield plan, builds_count, runs_count, caseruns_count, \
                    self.walk_status_matrix_section(builds)

        return {
            'plans_count': plans_count,
            'runs_count': runs_subtotal.total,
            'case_runs_count': case_runs_count,
            'reports': walk_status_matrix_rows(),
        }

    def walk_status_matrix_section(self, status_matrix_section):
        prev_build = None

        ordered_builds = sorted(status_matrix_section.iteritems(),
                                key=lambda item: item[0].pk)
        for build, runs in ordered_builds:
            build_rowspan = runs.leaf_values_count(value_in_row=True)

            ordered_runs = sorted(runs.iteritems(),
                                  key=lambda item: item[0].pk)

            for run, status_subtotal in ordered_runs:
                if build == prev_build:
                    _build = (build, None)
                else:
                    _build = (build, build_rowspan)
                    prev_build = build
                yield _build, run, status_subtotal

    def status_matrix(self, form):
        sql, params = self._prepare_sql(
            form, sqls.by_plan_build_detail_status_matrix)
        rows = SQLExecution(sql, params, with_field_name=False).rows
        status_matrix = GroupByResult()

        for row in rows:
            plan_id, plan_name, build_id, build_name, \
                run_id, run_summary, status_name, total_count = row

            plan = TestPlan(pk=plan_id, name=plan_name)
            builds = status_matrix.setdefault(plan, GroupByResult())

            build = TestBuild(pk=build_id, name=build_name)
            runs = builds.setdefault(build, GroupByResult(

            ))

            run = TestRun(pk=run_id, summary=run_summary)
            status_subtotal = runs.setdefault(run, GroupByResult())
            status_subtotal[status_name] = total_count

        return status_matrix


class TestingReportCaseRunsData(object):
    '''Data of case runs from testing report

    Case runs will be search by following criteria,

        - criteria from testing report search form, r_product, r_build,
          r_created_since, r_created_before, and r_version.
        - run, the run in which the case is run
        - priority, case' priority
        - tester, who is responsible for testing the case. For convenient, 0
          means tester is None, and any other integers that is greater than
          0 represents a valid user ID. If tester does not appear, it means
          no need to treat tester as a search criteria.
        - status, case run status
        - plan_tag
    '''

    run_filter_criteria = {
        'r_product': ('run__build__product', do_nothing),
        'r_build': ('run__build__in', models_to_pks),
        'r_created_since': ('run__start_date__gte', do_nothing),
        'r_created_before': ('run__start_date__lte', do_nothing),
        'r_version': ('run__product_version__in', models_to_pks),
        'run': ('run__pk', do_nothing),
    }

    def _get_filter_criteria(self, form):
        '''Get filter criteria, only once during single request'''
        filter_criteria = getattr(self, '__filter_criteria', None)
        if filter_criteria is None:
            filter_criteria = self.runs_filter_criteria(form)
            filter_criteria.update(self.case_runs_filter_criteria(form))
            self.__filter_criteria = filter_criteria
        return filter_criteria

    def get_case_runs(self, form):
        filter_criteria = self._get_filter_criteria(form)
        qs = TestCaseRun.objects.filter(**filter_criteria)
        qs = qs.select_related('run', 'case', 'case__category')
        case_runs = qs.only('tested_by', 'assignee',
                            'run__run_id',
                            'run__plan',
                            'case__summary',
                            'case__is_automated',
                            'case__is_automated_proposed',
                            'case__category__name',
                            'case__priority',
                            'case_text_version',
                            'case_run_status',
                            'sortkey')

        return case_runs

    def get_related_testers(self, testers_ids):
        users = User.objects.filter(
            pk__in=testers_ids).values_list('pk', 'username').order_by('pk')
        return dict(users.iterator())

    def get_related_assignees(self, assignees_ids):
        users = User.objects.filter(
            pk__in=assignees_ids).values_list('pk', 'username').order_by('pk')
        return dict(users.iterator())

    def runs_filter_criteria(self, form):
        result = {}
        for criteria_field, expr in self.run_filter_criteria.iteritems():
            value = form.cleaned_data[criteria_field]
            if value:
                result[expr[0]] = expr[1](value)

        plan_tag = form.cleaned_data['plan_tag']
        if plan_tag and plan_tag != 'untagged':
            result['run__plan__tag__name'] = plan_tag

        return result

    def case_runs_filter_criteria(self, form):
        filter_criteria = {}

        priority = form.cleaned_data['priority']
        if priority:
            filter_criteria['case__priority__pk'] = priority

        tester = form.cleaned_data['tester']
        if tester is not None:
            if tester == 0:
                filter_criteria['tested_by'] = None
            else:
                filter_criteria['tested_by__pk'] = tester

        status = form.cleaned_data['status']
        if status:
            status_id = TestCaseRunStatus.get_names_ids()[status.upper()]
            filter_criteria['case_run_status'] = status_id

        return filter_criteria
