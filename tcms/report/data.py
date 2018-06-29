# -*- coding: utf-8 -*-
from collections import defaultdict
from itertools import groupby

from django_comments.models import Comment
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.db.models import Count, F

from tcms.management.models import Priority
from tcms.testcases.models import TestCase
from tcms.testcases.models import Bug
from tcms.testcases.forms import AUTOMATED_SERCH_CHOICES
from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestCaseRun
from tcms.testruns.models import TestCaseRunStatus
from tcms.testruns.models import TestRun
from tcms.core.db import GroupByResult
from tcms.management.models import Build
from tcms.management.models import Tag

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
    return [model.pk for model in models]  # pylint: disable=avoid-list-comprehension


def model_to_pk(model):
    return model.pk


def do_nothing(value):
    return value


class ProductBuildReportData(object):
    """Report data by builds of a Product"""

    def finished_runs_count(self, product_id):
        return self.total_runs_count(product_id, True)

    def finished_caseruns_count(self, product_id):
        return self.caseruns_count(
            product_id,
            {'case_run_status__name__in': TestCaseRunStatus.complete_status_names}
        )

    def failed_caseruns_count(self, product_id):
        return self.caseruns_count(
            product_id,
            {'case_run_status__name': 'FAILED'}
        )

    @staticmethod
    def caseruns_count(product_id, condition=None):
        case_runs = {}
        query = TestCaseRun.objects.filter(
            build__product=product_id
        )
        if condition:
            query = query.filter(**condition)
        query = query.values('build').annotate(
            total_count=Count('pk')
        ).order_by('build')
        for row in query:
            case_runs[row['build']] = row['total_count']
        return case_runs

    @staticmethod
    def caserun_status_subtotal(product_id, build_id):
        test_case_runs = TestCaseRun.objects.filter(
            run__plan__product=product_id,
            run__build=build_id
        ).values(
            'case_run_status__name'
        ).annotate(status_count=Count('case_run_status__name'))

        subtotal = {}
        total = 0
        for test_case_run in test_case_runs:
            subtotal[test_case_run['case_run_status__name']] = test_case_run['status_count']
            total += test_case_run['status_count']
        subtotal['TOTAL'] = total

        return subtotal

    @staticmethod
    def total_runs_count(product_id, finished=False):
        builds = {}
        query = TestRun.objects.filter(build__product=product_id)
        if finished:
            query = query.filter(stop_date__isnull=False)
        query = query.values('build').annotate(
            total_count=Count('pk')
        ).order_by('build')
        for row in query:
            builds[row['build']] = row['total_count']
        return builds


class ProductComponentReportData(object):

    def failed_case_runs_count(self, product_id):
        return self.total_cases(
            product_id,
            {
                'case_run_status__name__in':
                    TestCaseRunStatus.failure_status_names
            }
        )

    def finished_case_runs_count(self, product_id):
        return self.total_cases(
            product_id,
            {
                'case_run_status__name__in':
                    TestCaseRunStatus.complete_status_names
            }
        )

    @staticmethod
    def case_runs_count(component_id):
        subtotal = {}
        total = 0
        query = TestCaseRun.objects.filter(
            case__component=component_id
        ).values(
            'case_run_status__name'
        ).annotate(status_count=Count('case_run_status__name'))

        for row in query:
            subtotal[row['case_run_status__name']] = row['status_count']
            total += row['status_count']
        subtotal['TOTAL'] = total
        return subtotal

    @staticmethod
    def total_cases(product_id, condition=None):
        """
        :param product_id: ID of the product
        :type product_id: number
        :param condition: additional conditions to be added to the query
        :type condition: dict
        """
        total = {}
        query = TestCaseRun.objects.filter(
            case__component__product=product_id
        )
        if condition:
            query = query.filter(**condition)
        query = query.values('case__component').annotate(
            total_count=Count('pk')
        ).order_by('case__component')

        for row in query:
            total[row['case__component']] = row['total_count']
        return total


class ProductVersionReportData(object):
    """Report data by versions of a Product"""

    def finished_case_runs_subtotal(self, product_id):
        return self.case_runs_subtotal(
            product_id,
            {
                'case_run_status__name__in':
                    TestCaseRunStatus.complete_status_names
            }
        )

    def failed_case_runs_subtotal(self, product_id):
        return self.case_runs_subtotal(
            product_id,
            {
                'case_run_status__name__in':
                    TestCaseRunStatus.failure_status_names
            }
        )

    @staticmethod
    def plans_subtotal(product_id, condition=None):
        """
        :param product_id: ID of the Product
        :type product_id: number
        :param condition: additional conditions to be added to the query
        :type condition: dict
        """
        query = TestPlan.objects.filter(product=product_id)
        if condition:
            query = query.filter(**condition)
        query = query.values('product_version').annotate(
            total_count=Count('pk')
        ).order_by('product_version')

        total = {}
        for row in query:
            total[row['product_version']] = row['total_count']
        return total

    @staticmethod
    def runs_subtotal(product_id, running=True):
        total = {}
        test_runs = TestRun.objects.filter(
            plan__product=product_id,
            stop_date__isnull=running
        ).values(
            'product_version'
        ).annotate(
            total_count=Count('pk')
        ).order_by('product_version')

        for test_run in test_runs:
            total[test_run['product_version']] = test_run['total_count']
        return total

    @staticmethod
    def cases_subtotal(product_id):
        """
        :param product_id: ID of the Product
        :type product_id: number
        """
        total = {}
        test_cases = TestCase.objects.filter(
            plan__product=product_id
        ).values('plan__product_version').annotate(
            total_count=Count('pk')
        ).order_by('plan__product_version')

        for test_case in test_cases:
            total[test_case['plan__product_version']] = test_case['total_count']
        return total

    @staticmethod
    def case_runs_subtotal(product_id, condition=None):
        """
        :param product_id: ID of the Product
        :type product_id: number
        :param condition: additional conditions to be added to the query
        :type condition: dict
        """
        query = TestCaseRun.objects.filter(
            run__plan__product=product_id
        )
        if condition:
            query = query.filter(**condition)
        query = query.values('run__product_version').annotate(
            total_count=Count('pk')
        ).order_by('run__product_version')

        total = {}
        for row in query:
            total[row['run__product_version']] = row['total_count']
        return total

    @staticmethod
    def case_runs_status_subtotal(product_id, version_id):
        test_case_runs = TestCaseRun.objects.filter(
            run__plan__product=product_id,
            run__plan__product_version=version_id
        ).values(
            'case_run_status__name'
        ).annotate(status_count=Count('case_run_status__name'))

        total = 0
        subtotal = {}
        for row in test_case_runs:
            subtotal[row['case_run_status__name']] = row['status_count']
            total += row['status_count']
        subtotal['TOTAL'] = total

        return subtotal


class CustomReportData(object):
    """Data for custom report

    In this data class, a major task is to construct INNER JOINS dynamically
    according to criteria selected by user.

    INNER JOINS include must-exist joins for getting data, and other potential
    ones that should be added according to criteria user specifies.

    One important thing is to ensure final INNER JOINS should be unique, so
    that no unnecessary table-join operation happens in database.
    """

    # All data are selected from TestCaseRuns, so following filters are
    # relative to that table.
    report_criteria = {
        'pk__in': ('build__in', models_to_pks),
        'product': ('build__product', model_to_pk),
        'build_run__product_version': ('run__product_version', model_to_pk),
        'build_run__plan__name__icontains': ('run__plan__name__icontains', do_nothing),
        'testcaserun__case__category': ('case__category', model_to_pk),
        'testcaserun__case__component': ('case__component', model_to_pk),
    }

    def __init__(self, form):
        self._form = form

    def _filter_query(self, query, filter_criteria):
        """Singleton method ensures queries are filtered only here

        @return: QuerySet
        """
        for field_name, value in self._form.cleaned_data.items():
            if not value:
                continue

            # filter query as requested in the filter criteria
            expr, value_conv = filter_criteria[field_name]
            args = {expr: value_conv(value)}
            query = query.filter(**args)

        return query

    def _get_builds(self):
        """Get builds statistics from valid search form.

        @param form: the form containing valid data
        @type form: L{CustomSearchForm}
        @return: queried test builds
        @rtype: L{QuerySet}
        """
        return self._filter_query(
            TestCaseRun.objects.values(
                'build',
                'build__name'
            ).annotate(
                runs_count=Count('run_id', distinct=True),
                plans_count=Count('run__plan', distinct=True),
                case_runs_count=Count('pk', distinct=True),
            ).order_by('build'),
            self.report_criteria
        )

    @staticmethod
    def automation_total(build_ids):
        """
        :param build_ids: list of IDs of the builds, by which the TestCaseRuns are filtered
        :type build_ids: list
        """
        automated_name_map = {}

        # convert tuples to map for easier indexing
        for _id, name in AUTOMATED_SERCH_CHOICES:
            if isinstance(_id, int):
                automated_name_map[_id] = name

        results = {}
        for obj in TestCaseRun.objects.filter(
                build__in=build_ids
            ).values('case__is_automated').distinct().annotate(
                total_count=Count('case__is_automated')):
            automation_id = obj['case__is_automated']
            results[automated_name_map[automation_id]] = obj['total_count']

        return results

    # ## Case run status matrix to show progress bar for each build ###

    @staticmethod
    def status_matrix(build_ids):
        """
        Case run status matrix used to render progress bar

        :param build_ids: list of IDs of the builds, by which the TestCaseRuns are filtered
        :type build_ids: list
        """

        test_case_runs = TestCaseRun.objects.filter(
            build__in=build_ids,
            case_run_status__name__in=('PASSED', 'FAILED')
        ).values(
            'build',
            'case_run_status__name'
        ).annotate(case_run_total=Count('case_run_status__name'))

        builds = {}
        for test_case_run in test_case_runs:
            bid = test_case_run['build']
            if bid not in builds.keys():
                builds[bid] = {}
            builds[bid][test_case_run['case_run_status__name']] = test_case_run['case_run_total']

        return builds


class CustomDetailsReportData(CustomReportData):
    """Data for custom details report

    Inherits from CustomReportData is becuase details report also need the
    summary header data and the progress bar for being viewed test build. You
    may treat the latter one as a subset of custom report.

    Besides above same data, details report also defines following methods to
    get specific data for detailed information to show to user.
    """

    # In detail report, there is only one selected test build at a time.
    report_criteria = CustomReportData.report_criteria.copy()
    report_criteria['pk__in'] = ('build', model_to_pk)

    @staticmethod
    def generate_status_matrix(build_ids):
        matrix_dataset = {}
        # TODO: replace defaultdict with GroupByResult
        status_total_line = defaultdict(int)

        rows = TestCaseRun.objects.filter(
            build__in=build_ids
        ).values(
            'run__plan',
            'run__plan__name',
            'run',
            'run__summary',
            'case_run_status__name'
        ).annotate(
            total_count=Count('pk')
        ).order_by('run__plan', 'run')

        for row in rows:
            plan_id = row['run__plan']
            plan_name = row['run__plan__name']
            run_id = row['run']
            run_summary = row['run__summary']
            status_name = row['case_run_status__name']
            status_count = row['total_count']

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

    @staticmethod
    def get_case_runs(build_ids, status_ids):
        """Get case runs according to builds and status

        @param build_ids: IDs of builds
        @type build_ids: list or tuple
        @param status_ids: IDs of case run status
        @type status_ids: list or tuple
        @return: queried case runs
        @rtype: L{QuerySet}
        """
        return TestCaseRun.objects.filter(
            run__build__in=build_ids,
            case_run_status_id__in=status_ids
        ).select_related(
            'run',
            'case',
            'tested_by'
        ).only(
            'run',
            'case__summary',
            'case__category__name',
            'tested_by__username',
            'close_date'
        ).order_by('case')

    @staticmethod
    def get_case_runs_bugs(build_ids, status_ids):
        """Get case runs' bugs according to builds and status

        @param build_ids: IDs of builds
        @type build_ids: list or tuple
        @param status_ids: IDs of case run status
        @type status_ids: list or tuple
        @return: mapping between case run ID and its bugs
        @rtype: dict
        """
        bugs = Bug.objects.filter(
            case_run__run__build__in=build_ids,
            case_run__case_run_status_id__in=status_ids
        ).select_related(
            'bug_system'
        ).only('bug_id',
               'bug_system__url_reg_exp',
               'case_run')

        case_run_bugs = {}
        for case_run_id, bugs in groupby(bugs, key=lambda bug: bug.case_run_id):
            case_run_bugs[case_run_id] = list(bugs)

        return case_run_bugs

    @staticmethod
    def get_case_runs_comments(build_ids, status_ids):
        """Get case runs' bugs according to builds and status

        @param build_ids: IDs of builds
        @type build_ids: list or tuple
        @param status_ids: IDs of case run status
        @type status_ids: list or tuple
        @return: mapping between case run ID and its comments
        @rtype: dict
        """
        content_type = ContentType.objects.get_for_model(TestCaseRun)
        rows = Comment.objects.filter(
            site=settings.SITE_ID,
            content_type=content_type.pk,
            is_public=True,
            is_removed=False,
            object_pk__in=TestCaseRun.objects.filter(
                build__in=build_ids,
                case_run_status__in=status_ids
            )
        ).annotate(
            case_run_id=F('object_pk')
        ).values(
            'user__username',
            'case_run_id',
            'submit_date',
            'comment'
        ).order_by('case_run_id')

        case_run_comments = {}
        for case_run_id, comments in groupby(rows, key=lambda row: row['case_run_id']):
            case_run_comments[case_run_id] = list(comments)

        return case_run_comments


class TestingReportBaseData(object):
    """Base data of various testing report"""
    # filter criteria is against TestCaseRun
    report_criteria = {
        'r_product': ('build__product', lambda obj: obj.pk),
        'r_build': ('build__in', models_to_pks),
        'r_created_since': ('run__start_date__gte', do_nothing),
        'r_created_before': ('run__start_date__lte', do_nothing),
        'r_version': ('run__product_version__in', models_to_pks),
    }

    def _filter_query(self, form, query):
        for field, condition in self.report_criteria.items():
            param = form.cleaned_data[field]
            if param:
                expr, value_conv = condition
                args = {expr: value_conv(param)}
                query = query.filter(**args)
        return query

    # ## Report data generation ###

    def _get_report_data(self, form, builds, builds_selected):
        """
        The core method to generate report data. Remain for subclass to
        implement

        @param form: the valid form containing report criteria
        @type form: L{RunForm}
        @param builds: sequence of Builds, either selected by user or the
            all builds of selected product
        @type builds: list or tuple
        @param builds_select: whether the builds are selected by user
        @type builds_selected: bool
        @return: the report data
        @rtype: dict
        """
        raise NotImplementedError

    def get_report_data(self, form):
        """Core method to get report data exported to testing report view"""
        builds, builds_selected = self._get_builds(form)
        data = self._get_report_data(form, builds, builds_selected)
        data.update({
            'builds_selected': builds_selected,
            'builds': builds,
        })
        return data

    @staticmethod
    def _get_builds(form):
        """Get selected or all product's builds for display"""
        builds = form.cleaned_data['r_build']
        builds_selected = len(builds) > 0
        if not builds:
            product = form.cleaned_data['r_product']
            builds = Build.objects.filter(product=product).only('name')
        return builds, builds_selected

    # ## Shared report data ###

    def plans_count(self, form):
        query = self._filter_query(
            form,
            TestCaseRun.objects.values('run__plan').distinct()
        )
        return query.count()

    def runs_count(self, form):
        query = self._filter_query(
            form,
            TestCaseRun.objects.values('run').distinct()
        )
        return query.count()

    # ## Helper methods ###

    @staticmethod
    def get_build_names(build_ids):
        return dict(Build.objects.filter(
            pk__in=build_ids).values_list('pk', 'name').iterator())

    @staticmethod
    def get_usernames(user_ids):
        return dict(User.objects.filter(
            id__in=user_ids).values_list('id', 'username').iterator())


class TestingReportByCaseRunTesterData(TestingReportBaseData):
    """Data for testing report of By Case Run Tester"""

    def _get_report_data(self, form, builds, builds_selected):
        if builds_selected:
            return self._get_report_data_with_builds(form, builds)
        return self._get_report_data_without_builds_selected(form)

    def _get_report_data_without_builds_selected(self, form):
        """Get report data when user does not select any build"""
        plans_count = self.plans_count(form)
        runs_count = self.runs_count(form)
        status_matrix = self.status_matrix(form)
        runs_subtotal = self.runs_subtotal(form)

        tested_by_usernames = self.get_usernames(status_matrix.keys())

        def walk_status_matrix_rows():
            tested_by_ids = sorted(status_matrix.items(),
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
        """Get report data when user selects one or more builds

        @param form: the valid form containing report criteria
        @type form: L{RunForm}
        @param builds: selected builds by user
        @type builds: list
        @return: report data containing all necessary data grouped by selected
            builds and tested_bys
        @rtype: dict
        """
        plans_count = self.plans_count(form)
        runs_count = self.runs_count(form)
        status_matrix = self.status_matrix_groupby_builds(form)
        runs_subtotal = self.runs_subtotal_groupby_builds(form)

        # Get related tested_by's username. Don't need duplicated user ids.
        tested_by_ids = []
        for _build_id, tested_bys in status_matrix.items():
            tested_by_ids += tested_bys.keys()
        tested_by_ids = set(tested_by_ids)

        build_names = self.get_build_names(build.pk for build in builds)
        tested_by_names = self.get_usernames(tested_by_ids)

        def walk_status_matrix_rows():
            """For rendering template, walk through status matrix row by row"""
            prev_build = None
            builds = sorted(status_matrix.items(),
                            key=lambda item: item[0])
            for build_id, tested_by_ids in builds:
                build_rowspan = len(tested_by_ids)
                tested_by_ids = sorted(tested_by_ids.items(),
                                       key=lambda item: item[0] or 0)
                for tested_by_id, status_subtotal in tested_by_ids:
                    if build_id not in runs_subtotal:
                        runs_count = 0
                    elif tested_by_id not in runs_subtotal[build_id]:
                        runs_count = 0
                    else:
                        runs_count = runs_subtotal[build_id][tested_by_id]

                    build = Build(pk=build_id,
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
        status_matrix = GroupByResult({})
        query = self._filter_query(
            form,
            TestCaseRun.objects.values(
                'tested_by',
                'case_run_status__name'
            ).annotate(
                total_count=Count('pk')
            )
        )

        for row in query:
            tested_by_id = row['tested_by']
            if tested_by_id is None:
                tested_by_id = 0
            name = row['case_run_status__name']
            total_count = row['total_count']

            status_subtotal = status_matrix.setdefault(
                tested_by_id, GroupByResult({}))
            status_subtotal[name] = total_count

        return status_matrix

    def status_matrix_groupby_builds(self, form):
        builds = GroupByResult({})
        query = self._filter_query(
            form,
            TestCaseRun.objects.values(
                'build',
                'tested_by',
                'case_run_status__name'
            ).annotate(
                total_count=Count('pk')
            )
        )

        for row in query:
            build_id = row['build']
            tested_by_id = row['tested_by']
            name = row['case_run_status__name']
            total_count = row['total_count']

            tested_by_ids = builds.setdefault(build_id, GroupByResult({}))
            status_subtotal = tested_by_ids.setdefault(tested_by_id,
                                                       GroupByResult({}))
            status_subtotal[name] = total_count

        return builds

    def runs_subtotal(self, form):
        result = {}
        query = self._filter_query(
            form,
            TestCaseRun.objects.values('tested_by', 'run').distinct()
        )
        for row in query:
            tested_by_id = row['tested_by']
            if tested_by_id in result.keys():
                result[tested_by_id] += 1
            else:
                result[tested_by_id] = 1

        return result

    def runs_subtotal_groupby_builds(self, form):
        builds = GroupByResult({})
        query = self._filter_query(
            form,
            TestCaseRun.objects.values('tested_by', 'run', 'build').distinct()
        )

        for row in query:
            build_id = row['build']
            tested_by_id = row['tested_by']

            tested_by_ids = builds.setdefault(build_id, GroupByResult({}))
            if tested_by_id in tested_by_ids.keys():
                tested_by_ids[tested_by_id] += 1
            else:
                tested_by_ids[tested_by_id] = 1

        return builds


class TestingReportByCasePriorityData(TestingReportBaseData):
    """Data for testing report By Case Priority"""

    def _get_report_data(self, form, builds, builds_selected):
        plans_count = self.plans_count(form)
        runs_count = self.runs_subtotal(form)
        status_matrix = self.status_matrix(form)

        build_ids = status_matrix.keys()
        builds_names = self.get_build_names(build_ids)

        def walk_status_matrix_rows():
            prev_build_id = None
            ordered_builds = sorted(status_matrix.items(),
                                    key=lambda item: item[0])
            for build_id, priorities in ordered_builds:
                build_rowspan = len(priorities)
                ordered_priorities = sorted(priorities.items(),
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
        query = self._filter_query(
            form,
            TestCaseRun.objects.values('run').distinct()
        )
        return query.count()

    def status_matrix(self, form):
        builds = GroupByResult()
        query = self._filter_query(
            form,
            TestCaseRun.objects.values(
                'build',
                'case__priority',
                'case__priority__value',
                'case_run_status__name'
            ).annotate(total_count=Count('pk'))
        )

        for row in query:
            build_id = row['build']
            priority_id = row['case__priority']
            priority_value = row['case__priority__value']
            name = row['case_run_status__name']
            total_count = row['total_count']
            priorities = builds.setdefault(build_id, GroupByResult())
            priority = Priority(pk=priority_id, value=priority_value)
            status_subtotal = priorities.setdefault(priority, GroupByResult())
            status_subtotal[name] = total_count

        return builds


class TestingReportByPlanTagsData(TestingReportBaseData):
    """Data for testing report By Plan Tag"""

    def _get_report_data(self, form, builds, builds_selected):
        plans_count = self.plans_count(form)
        runs_count = self.runs_count(form)
        status_matrix = self.passed_failed_case_runs_subtotal(form)
        plans_subtotal = self.plans_subtotal(form)
        runs_subtotal = self.runs_subtotal(form)
        tags_names = self.get_tags_names(status_matrix.keys())

        def walk_status_matrix_rows():
            ordered_tags = sorted(status_matrix.items(),
                                  key=lambda item: item[0])
            for tag_id, status_subtotal in ordered_tags:
                yield tags_names.get(tag_id, ''), \
                    plans_subtotal.get(tag_id, 0), \
                    runs_subtotal.get(tag_id, 0), \
                    status_subtotal

        tags_names_sorted = []
        for key in sorted(tags_names.keys()):
            tags_names_sorted.append(tags_names[key])

        return {
            'plans_count': plans_count,
            'runs_count': runs_count,
            'reports': walk_status_matrix_rows(),

            # This is only used for displaying tags in report
            'tags_names': tags_names_sorted
        }

    def plans_subtotal(self, form):
        result = {}
        query = self._filter_query(
            form,
            TestCaseRun.objects.values(
                'run__plan__tag'
            ).annotate(
                total_count=Count('run__plan', distinct=True)
            )
        )
        for row in query:
            result[row['run__plan__tag']] = row['total_count']
        return result

    def runs_subtotal(self, form):
        result = {}
        query = self._filter_query(
            form,
            TestCaseRun.objects.values(
                'run__plan__tag'
            ).annotate(
                total_count=Count('run', distinct=True)
            )
        )
        for row in query:
            result[row['run__plan__tag']] = row['total_count']
        return result

    def passed_failed_case_runs_subtotal(self, form):  # pylint: disable=invalid-name
        query = self._filter_query(
            form,
            TestCaseRun.objects.values(
                'run__plan__tag', 'case_run_status__name'
            ).filter(case_run_status__name__in=['PASSED', 'FAILED']).annotate(
                total_count=Count('case_run_status')
            )
        )

        tags = GroupByResult()
        for row in query:
            tag_id = row['run__plan__tag']
            name = row['case_run_status__name']
            total_count = row['total_count']

            status_subtotal = tags.setdefault(tag_id, GroupByResult())
            status_subtotal[name] = total_count

        from pprint import pprint
        pprint(tags)

        return tags

    @staticmethod
    def get_tags_names(tag_ids):
        """Get tags names from status matrix"""

        names = dict(Tag.objects.filter(
            pk__in=tag_ids).values_list('pk', 'name').iterator())
        # The existence of None tells us the fact that there are plans without
        # any tag. So, name it untagged.
        if None in tag_ids:
            names[None] = 'untagged'
        return names


class TestingReportByPlanTagsDetailData(TestingReportByPlanTagsData):
    """Detail data for testing report By Plan Tag"""

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
            ordered_builds = sorted(status_matrix.items(),
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

    def status_matrix(self, form):
        status_matrix = GroupByResult()
        query = self._filter_query(
            form,
            TestCaseRun.objects.values(
                'build', 'build__name',
                'run__plan__tag',
                'run__plan', 'run__plan__name',
                'run', 'run__summary',
                'case_run_status__name'
            ).annotate(total_count=Count('pk'))
        )

        for row in query:
            tag_id = row['run__plan__tag']
            build_id = row['build']
            build_name = row['build__name']
            plan_id = row['run__plan']
            plan_name = row['run__plan__name']
            run_id = row['run']
            run_summary = row['run__summary']
            status_name = row['case_run_status__name']
            total_count = row['total_count']

            builds = status_matrix.setdefault(tag_id, GroupByResult())
            plans = builds.setdefault(Build(pk=build_id, name=build_name),
                                      GroupByResult())
            runs = plans.setdefault(TestPlan(pk=plan_id, name=plan_name),
                                    GroupByResult())
            status_subtotal = runs.setdefault(
                TestRun(pk=run_id, summary=run_summary), GroupByResult())
            status_subtotal[status_name] = total_count

        return status_matrix

    def case_runs_total(self, form):
        query = self._filter_query(
            form,
            TestCaseRun.objects.all()
        )
        return query.count()

    @staticmethod
    def walk_status_matrix_rows(root_matrix):
        """Walk status matrix row by row"""

        def sort_key(item):
            return item[0].pk

        prev_build = None
        prev_plan = None

        ordered_builds = sorted(root_matrix.items(), key=sort_key)
        for build, plans in ordered_builds:
            ordered_plans = sorted(plans.items(), key=sort_key)
            build_rowspan = plans.leaf_values_count(value_in_row=True)
            for plan, runs in ordered_plans:
                ordered_runs = sorted(runs.items(), key=sort_key)
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


class TestingReportByPlanBuildData(TestingReportBaseData):
    """Data of testing report By Plan Build"""

    def _get_report_data(self, form, builds, builds_selected):
        plans_count = self.plans_count(form)
        builds_subtotal = self.builds_subtotal(form)
        runs_subtotal = self.runs_subtotal(form)
        status_matrix = self.status_matrix(form)

        def walk_status_matrix_rows():
            ordered_plans = sorted(status_matrix.items(),
                                   key=lambda item: item[0].pk)
            for plan, _ in ordered_plans:
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
                      sorted(status_matrix.items(),
                             key=lambda item: item[0].pk))
        }

    def builds_subtotal(self, form):
        result = GroupByResult()
        query = self._filter_query(
            form,
            TestCaseRun.objects.values(
                'run__plan',
                'run__plan__name'
            ).annotate(
                total_count=Count('build', distinct=True)
            )
        )

        for row in query:
            plan_id = row['run__plan']
            plan_name = row['run__plan__name']
            builds_count = row['total_count']
            plan = TestPlan(pk=plan_id, name=plan_name)
            result[plan] = builds_count

        return result

    def runs_subtotal(self, form):
        result = GroupByResult()
        query = self._filter_query(
            form,
            TestCaseRun.objects.values(
                'run__plan',
                'run__plan__name'
            ).annotate(
                total_count=Count('run', distinct=True)
            )
        )

        for row in query:
            plan_id = row['run__plan']
            plan_name = row['run__plan__name']
            runs_count = row['total_count']
            plan = TestPlan(pk=plan_id, name=plan_name)
            result[plan] = runs_count
        return result

    def status_matrix(self, form):
        status_matrix = GroupByResult()
        query = self._filter_query(
            form,
            TestCaseRun.objects.values(
                'run__plan',
                'run__plan__name',
                'case_run_status__name'
            ).filter(
                case_run_status__name__in=('PASSED', 'FAILED')
            ).annotate(
                total_count=Count('run', distinct=True)
            )
        )

        for row in query:
            plan_id = row['run__plan']
            plan_name = row['run__plan__name']
            status_name = row['case_run_status__name']
            total_count = row['total_count']
            plan = TestPlan(pk=plan_id, name=plan_name)
            status_subtotal = status_matrix.setdefault(plan, GroupByResult())
            status_subtotal[status_name] = total_count

        return status_matrix


class TestingReportByPlanBuildDetailData(TestingReportByPlanBuildData):
    """Detail data of testing report By Plan Build Detail"""

    def _get_report_data(self, form, builds, builds_selected):
        plans_count = self.plans_count(form)
        builds_subtotal = self.builds_subtotal(form)
        runs_subtotal = self.runs_subtotal(form)
        status_matrix = self.status_matrix(form)

        case_runs_count = status_matrix.total
        # Force to calculate leaf values count to cache in each level
        status_matrix.leaf_values_count(value_in_row=True)

        def walk_status_matrix_rows():
            ordered_plans = sorted(status_matrix.items(),
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

    def status_matrix(self, form):
        query = self._filter_query(
            form,
            TestCaseRun.objects.values(
                'run__plan', 'run__plan__name',
                'build', 'build__name',
                'run', 'run__summary',
                'case_run_status__name'
            ).annotate(total_count=Count('pk'))
        )
        status_matrix = GroupByResult()

        for row in query:
            plan_id = row['run__plan']
            plan_name = row['run__plan__name']
            build_id = row['build']
            build_name = row['build__name']
            run_id = row['run']
            run_summary = row['run__summary']
            status_name = row['case_run_status__name']
            total_count = row['total_count']

            plan = TestPlan(pk=plan_id, name=plan_name)
            builds = status_matrix.setdefault(plan, GroupByResult())

            build = Build(pk=build_id, name=build_name)
            runs = builds.setdefault(build, GroupByResult())

            run = TestRun(pk=run_id, summary=run_summary)
            status_subtotal = runs.setdefault(run, GroupByResult())
            status_subtotal[status_name] = total_count

        return status_matrix

    @staticmethod
    def walk_status_matrix_section(status_matrix_section):
        prev_build = None

        ordered_builds = sorted(status_matrix_section.items(),
                                key=lambda item: item[0].pk)
        for build, runs in ordered_builds:
            build_rowspan = runs.leaf_values_count(value_in_row=True)

            ordered_runs = sorted(runs.items(),
                                  key=lambda item: item[0].pk)

            for run, status_subtotal in ordered_runs:
                if build == prev_build:
                    _build = (build, None)
                else:
                    _build = (build, build_rowspan)
                    prev_build = build
                yield _build, run, status_subtotal


class TestingReportCaseRunsData(object):
    """Data of case runs from testing report

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
    """

    run_filter_criteria = {
        'r_product': ('run__build__product', do_nothing),
        'r_build': ('run__build__in', models_to_pks),
        'r_created_since': ('run__start_date__gte', do_nothing),
        'r_created_before': ('run__start_date__lte', do_nothing),
        'r_version': ('run__product_version__in', models_to_pks),
        'run': ('run__pk', do_nothing),
    }

    def _get_filter_criteria(self, form):
        """Get filter criteria, only once during single request"""

        filter_criteria = self.runs_filter_criteria(form)
        filter_criteria.update(self.case_runs_filter_criteria(form))

        return filter_criteria

    def get_case_runs(self, form):
        filter_criteria = self._get_filter_criteria(form)
        return TestCaseRun.objects.filter(**filter_criteria).select_related(
            'run', 'case').only('tested_by',
                                'assignee',
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

    def runs_filter_criteria(self, form):
        result = {}
        for criteria_field, expr in self.run_filter_criteria.items():
            value = form.cleaned_data[criteria_field]
            if value:
                result[expr[0]] = expr[1](value)

        plan_tag = form.cleaned_data['plan_tag']
        if plan_tag and plan_tag != 'untagged':
            result['run__plan__tag__name'] = plan_tag

        return result

    @staticmethod
    def get_related_users(testers_ids):
        users = User.objects.filter(
            pk__in=testers_ids).values_list('pk', 'username').order_by('pk')
        return dict(users.iterator())

    @staticmethod
    def case_runs_filter_criteria(form):
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
