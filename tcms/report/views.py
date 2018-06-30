# -*- coding: utf-8 -*-

from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.db.models import Count, OuterRef, Subquery
from django.http import Http404
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic import View

from .forms import CustomSearchDetailsForm
from tcms.management.models import Priority
from tcms.management.models import Product
from tcms.testruns.models import TestRun, TestCaseRunStatus, TestCaseRun
from tcms.report.forms import TestingReportForm
from tcms.report.forms import TestingReportCaseRunsListForm
from tcms.report.data import CustomDetailsReportData
from tcms.report.data import CustomReportData
from tcms.report.data import ProductBuildReportData
from tcms.report.data import ProductComponentReportData
from tcms.report.data import ProductVersionReportData
from tcms.report.data import TestingReportByCasePriorityData
from tcms.report.data import TestingReportByCaseRunTesterData
from tcms.report.data import TestingReportByPlanBuildData
from tcms.report.data import TestingReportByPlanBuildDetailData
from tcms.report.data import TestingReportByPlanTagsData
from tcms.report.data import TestingReportByPlanTagsDetailData
from tcms.report.data import TestingReportCaseRunsData
from tcms.report.forms import CustomSearchForm
from tcms.search import fmt_queries, remove_from_request_path


def overall(request, template_name='report/list.html'):
    """Overall of products report"""
    cases_count_query = Product.objects.filter(pk=OuterRef('pk')) \
                                       .annotate(cases_num=Count('plan__case')) \
                                       .values('cases_num')
    products = Product.objects.annotate(plans_count=Count('plan', distinct=True),
                                        runs_count=Count('plan__run', distinct=True),
                                        cases_count=Subquery(cases_count_query))

    context_data = {
        'products': products
    }
    return render(request, template_name, context_data)


def overview(request, product_id, template_name='report/overview.html'):
    """Product for a product"""
    try:
        product = Product.objects.only('name').get(pk=product_id)
    except Product.DoesNotExist as error:
        raise Http404(error)

    query = TestRun.objects.filter(plan__product=product_id)
    runs_count = {
        'TOTAL': query.count(),
        'finished': query.filter(stop_date__isnull=False).count(),
    }
    runs_count['running'] = runs_count['TOTAL'] - runs_count['finished']

    query = TestCaseRun.objects.filter(run__plan__product=product_id)
    caserun_status_count = {}
    total = 0
    for row in TestCaseRun.objects.filter(
            run__plan__product=product_id
        ).values('case_run_status__name').annotate(
            status_count=Count('case_run_status__name')):
        caserun_status_count[row['case_run_status__name']] = row['status_count']
        total += row['status_count']
    caserun_status_count['TOTAL'] = total

    context_data = {
        'SUB_MODULE_NAME': 'overview',
        'product': product,
        'runs_count': runs_count,
        'case_run_count': caserun_status_count,
    }
    return render(request, template_name, context_data)


class ProductVersionReport(TemplateView, ProductVersionReportData):
    template_name = 'report/version.html'

    def get(self, request, product_id):
        try:
            self.product = Product.objects.only('name').get(pk=product_id)

            version_id = request.GET.get('version_id')
            if version_id is not None:
                qs = self.product.version.only('value')
                self.selected_version = qs.get(pk=int(version_id))
        except (TypeError, ValueError, ObjectDoesNotExist) as error:
            raise Http404(error)

        return super(ProductVersionReport, self).get(request, product_id)

    def get_context_data(self, **kwargs):
        versions = self.product.version.only('product', 'value')
        product_id = self.product.pk

        plans_subtotal = self.plans_subtotal(product_id)
        running_runs_subtotal = self.runs_subtotal(product_id, True)
        finished_runs_subtotal = self.runs_subtotal(product_id, False)
        cases_subtotal = self.cases_subtotal(product_id)
        case_runs_subtotal = self.case_runs_subtotal(product_id)
        finished_case_runs_subtotal = \
            self.finished_case_runs_subtotal(product_id)
        failed_case_runs_subtotal = self.failed_case_runs_subtotal(product_id)

        for version in versions:
            vid = version.pk
            version.plans_count = plans_subtotal.get(vid, 0)
            version.running_runs_count = running_runs_subtotal.get(vid, 0)
            version.finished_runs_count = finished_runs_subtotal.get(vid, 0)
            version.cases_count = cases_subtotal.get(vid, 0)
            version.failed_case_runs_count = failed_case_runs_subtotal.get(vid,
                                                                           0)

            m = finished_case_runs_subtotal.get(vid, 0)
            n = case_runs_subtotal.get(vid, 0)
            if m and n:
                version.case_run_percent = round(m * 100.0 / n, 1)
            else:
                version.case_run_percent = .0

        case_runs_status_subtotal = None
        selected_version = getattr(self, 'selected_version', None)
        if selected_version is not None:
            case_runs_status_subtotal = self.case_runs_status_subtotal(
                product_id, selected_version.pk)

        data = super(ProductVersionReport, self).get_context_data(**kwargs)
        data.update({
            'SUB_MODULE_NAME': 'version',
            'product': self.product,
            'versions': versions,
            'version': selected_version,
            'case_runs_status_subtotal': case_runs_status_subtotal,
        })

        return data


class ProductBuildReport(TemplateView, ProductBuildReportData):
    template_name = 'report/build.html'

    def get(self, request, product_id):
        try:
            self.product = Product.objects.only('name').get(pk=product_id)

            build_id = request.GET.get('build_id')
            if build_id is not None:
                qs = self.product.build.only('name')
                self.selected_build = qs.get(pk=int(build_id))
        except (TypeError, ValueError, ObjectDoesNotExist) as error:
            raise Http404(error)

        return super(ProductBuildReport, self).get(request, product_id)

    def get_context_data(self, **kwargs):
        builds = self.product.build.only('product', 'name')

        pid = self.product.pk
        builds_total_runs = self.total_runs_count(pid)
        builds_finished_runs = self.finished_runs_count(pid)
        builds_finished_caseruns = self.finished_caseruns_count(pid)
        builds_caseruns = self.caseruns_count(pid)
        builds_failed_caseruns = self.failed_caseruns_count(pid)

        for build in builds:
            bid = build.pk
            build.total_runs = builds_total_runs.get(bid, 0)
            build.finished_runs = builds_finished_runs.get(bid, 0)
            build.failed_case_run_count = builds_failed_caseruns.get(bid, 0)

            n = builds_finished_caseruns.get(bid, 0)
            m = builds_caseruns.get(bid, 0)
            if n and m:
                build.finished_case_run_percent = round(n * 100.0 / m, 1)
            else:
                build.finished_case_run_percent = .0

        case_runs_status_subtotal = None
        selected_build = getattr(self, 'selected_build', None)
        if selected_build is not None:
            case_runs_status_subtotal = self.caserun_status_subtotal(
                pid, selected_build.pk)

        data = super(ProductBuildReport, self).get_context_data(**kwargs)
        data.update({
            'SUB_MODULE_NAME': 'build',
            'product': self.product,
            'builds': builds,
            'build': selected_build,
            'case_runs_status_subtotal': case_runs_status_subtotal,
        })

        return data


class ProductComponentReport(TemplateView, ProductComponentReportData):
    template_name = 'report/component.html'

    def get(self, request, product_id):
        try:
            self.product = Product.objects.only('name').get(pk=product_id)

            component_id = request.GET.get('component_id')
            if component_id is not None:
                qs = self.product.component.only('name')
                self.selected_component = qs.get(pk=int(component_id))
        except (TypeError, ValueError, Product.DoesNotExist) as error:
            raise Http404(error)

        return super(ProductComponentReport, self).get(request, product_id)

    def get_context_data(self, **kwargs):
        components = self.product.component.select_related('product')
        components = components.only('name', 'product__name')

        pid = self.product.pk
        total_cases = self.total_cases(pid)
        failed_case_runs_count = self.failed_case_runs_count(pid)
        finished_case_runs_count = self.finished_case_runs_count(pid)

        for component in components:
            cid = component.pk
            component.total_cases = total_cases.get(cid, 0)
            component.failed_case_run_count = failed_case_runs_count.get(cid,
                                                                         0)

            n = finished_case_runs_count.get(cid, 0)
            m = component.total_cases
            if n and m:
                component.finished_case_run_percent = round(n * 100.0 / m, 1)
            else:
                component.finished_case_run_percent = 0

        # To show detail statistics upon case run status if user clicks a
        # component
        case_runs_status_subtotal = None
        selected_component = getattr(self, 'selected_component', None)
        if selected_component is not None:
            case_runs_status_subtotal = self.case_runs_count(
                selected_component.pk)

        data = super(ProductComponentReport, self).get_context_data(**kwargs)
        data.update({
            'SUB_MODULE_NAME': 'component',
            'product': self.product,
            'components': components,
            'component': selected_component,
            'case_runs_status_subtotal': case_runs_status_subtotal,
        })

        return data


class CustomReport(TemplateView):
    template_name = 'report/custom_search.html'
    form_class = CustomSearchForm
    data_class = CustomReportData

    def get(self, request):
        return super(CustomReport, self).get(request)

    def _get_search_form(self):
        req = self.request.GET
        form = self.form_class(req)
        form.populate(product_id=req.get('product'))
        return form

    def _do_search(self):
        return self.request.GET.get('a', '').lower() == 'search'

    def _report_data_context(self):
        form = self._get_search_form()
        context = {'form': form}

        if not form.is_valid():
            context.update({'builds': ()})
            return context

        self._data = self.data_class(form)

        builds = self._data._get_builds()
        build_ids = [b['build'] for b in builds]

        if builds:
            # Summary header data
            runs_total = 0
            case_runs_total = 0
            automation_total = self._data.automation_total(build_ids)

            # Status matrix used to render progress bar for each build
            status_matrix = self._data.status_matrix(build_ids)

            for build in builds:
                bid = build['build']
                runs_total += build['runs_count']

                # skip if we have builds for which there are TestRuns but
                # no cases have been executed
                if bid not in status_matrix:
                    continue

                passed_count = status_matrix[bid].get('PASSED', 0)
                failed_count = status_matrix[bid].get('FAILED', 0)

                c = build['case_runs_count']
                case_runs_total += build['case_runs_count']

                if c:
                    build['passed_case_runs_percent'] = passed_count * 100.0 / c
                    build['failed_case_runs_percent'] = failed_count * 100.0 / c
                else:
                    build['passed_case_runs_percent'] = .0
                    build['failed_case_runs_percent'] = .0

                build['passed_case_runs_count'] = passed_count
                build['failed_case_runs_count'] = failed_count

            context.update({
                'total_runs_count': runs_total,
                # todo: what if plan product was changed after the TR was created
                # with that particular build ?
                'total_plans_count': TestRun.objects.filter(
                    build__in=build_ids
                ).values('plan').distinct().count(),
                'total_count': case_runs_total,
                'manual_count': automation_total.get('Manual', 0),
                'auto_count': automation_total.get('Auto', 0),
                'both_count': automation_total.get('Both', 0),
            })

        context.update({'builds': builds})
        return context

    def _initial_context(self):
        return {
            'form': self.__class__.form_class(),
            'builds': (),
        }

    def _get_report_data_context(self):
        if self._do_search():
            return self._report_data_context()
        else:
            return self._initial_context()

    def get_context_data(self, **kwargs):
        data = super(CustomReport, self).get_context_data(**kwargs)
        data.update(self._get_report_data_context())
        return data


class CustomDetailReport(CustomReport):
    """Custom detail report

    Reuse CustomReport._search_context to get build and its summary statistics
    """

    template_name = 'report/custom_details.html'
    form_class = CustomSearchDetailsForm
    data_class = CustomDetailsReportData

    def _get_report_data_context(self):
        """Override to generate report by disabling check of argument a"""
        return self._report_data_context()

    def walk_matrix_row_by_row(self, matrix_dataset):
        status_total_line = None
        if None in matrix_dataset:
            status_total_line = matrix_dataset[None]
            del matrix_dataset[None]

        prev_plan = None
        # TODO: replace this with collections.OrderedDict after
        # upgrading to Python 2.7
        ordered_plans = sorted(matrix_dataset.items(),
                               key=lambda item: item[0].pk)
        for plan, runs in ordered_plans:
            plan_runs_count = len(runs)
            # TODO: and also this line
            ordered_runs = sorted(runs.items(),
                                  key=lambda item: item[0].pk)
            for run, status_subtotal in ordered_runs:
                if plan == prev_plan:
                    yield None, run, status_subtotal
                else:
                    yield (plan, plan_runs_count), run, status_subtotal
                    prev_plan = plan

        # Finally, yield the total line for rendering the complete report
        if status_total_line is not None:
            yield None, None, status_total_line

    def read_case_runs(self, build_ids, status_ids):
        """Generator for reading case runs and related objects"""
        case_runs = self._data.get_case_runs(build_ids, status_ids)
        bugs = self._data.get_case_runs_bugs(build_ids, status_ids)
        comments = self._data.get_case_runs_comments(build_ids, status_ids)

        for case_run in case_runs.iterator():
            related_bugs = bugs.get(case_run.pk, ())
            related_comments = comments.get(case_run.pk, ())
            yield case_run, related_bugs, related_comments

    def _report_data_context(self):
        data = {}
        form = self._get_search_form()

        if form.is_valid():
            summary_header_data = super(CustomDetailReport,
                                        self)._report_data_context()
            data.update(summary_header_data)

            build_ids = [build['build'] for build in data['builds']]

            status_matrix = self.walk_matrix_row_by_row(
                self._data.generate_status_matrix(build_ids)
            )

            status_ids = (TestCaseRunStatus.id_failed(),)
            failed_case_runs = self.read_case_runs(build_ids, status_ids)

            status_ids = (TestCaseRunStatus.id_blocked(),)
            blocked_case_runs = self.read_case_runs(build_ids, status_ids)

            data.update({
                'status_matrix': status_matrix,
                'failed_case_runs': failed_case_runs,
                'blocked_case_runs': blocked_case_runs,
            })
        else:
            data['report_errors'] = form.errors

        data['form'] = form
        return data


class TestingReportBase(TemplateView):
    """Base class for each type of report"""

    form_class = TestingReportForm

    def get(self, *args, **kwargs):
        return super(TestingReportBase, self).get(*args, **kwargs)

    def _get_form(self, data=None):
        product_id = self.request.GET.get('r_product')
        if data is not None:
            form = self.form_class(data)
        else:
            form = self.form_class()
        form.populate(product_id)
        return form

    def _init_context(self):
        """Provide very initial page without any report data

        Basically, in 2 senariors, user will be lead to this context

            - no parameters in query string
            - no report_type parameter in query string
        """
        return {
            'run_form': self._get_form(),
        }

    def _report_context(self):
        errors = None
        report_data = None
        queries = self.request.GET

        if queries:
            form = self._get_form(self.request.GET)

            if form.is_valid():
                queries = form.cleaned_data
                report_data = self.get_report_data(form)
            else:
                errors = form.errors

        queries = fmt_queries(queries)
        del queries['report type']
        request_path = remove_from_request_path(self.request, 'report_type')

        data = {
            'errors': errors,
            'queries': queries,
            'request_path': request_path,
            'run_form': form,
            'report_data': report_data,
        }

        if request_path:
            data['path_without_build'] = remove_from_request_path(request_path,
                                                                  'r_build')

        return data

    def get_context_data(self, **kwargs):
        data = super(TestingReportBase, self).get_context_data(**kwargs)

        if 'report_type' not in self.request.GET:
            context = self._init_context()
        else:
            context = self._report_context()

        data.update(context)
        data.update({
            'report_url': reverse('testing-report-case-runs'),
        })
        return data


class TestingReportByCaseRunTester(TestingReportBase,
                                   TestingReportByCaseRunTesterData):
    template_name = 'report/testing-report/per_build_report.html'


class TestingReportByCasePriority(TestingReportBase,
                                  TestingReportByCasePriorityData):
    template_name = 'report/testing-report/per_priority_report.html'


class TestingReportByPlanTags(TestingReportBase,
                              TestingReportByPlanTagsData):
    template_name = 'report/testing-report/by_plan_tag_with_rates.html'


class TestingReportByPlanTagsDetail(TestingReportBase,
                                    TestingReportByPlanTagsDetailData):
    template_name = 'report/testing-report/per_plan_tag.html'


class TestingReportByPlanBuild(TestingReportBase,
                               TestingReportByPlanBuildData):
    template_name = 'report/testing-report/by_plan_build_with_rates.html'


class TestingReportByPlanBuildDetail(TestingReportBase,
                                     TestingReportByPlanBuildDetailData):
    template_name = 'report/testing-report/per_plan_build.html'


class TestingReport(View):
    """Dispatch testing report according to report type"""

    testing_report_views = {
        None: TestingReportByCaseRunTester,
        'per_build_report': TestingReportByCaseRunTester,
        'per_priority_report': TestingReportByCasePriority,
        'runs_with_rates_per_plan_tag': TestingReportByPlanTags,
        'per_plan_tag_report': TestingReportByPlanTagsDetail,
        'runs_with_rates_per_plan_build': TestingReportByPlanBuild,
        'per_plan_build_report': TestingReportByPlanBuildDetail,
    }

    def _get_testing_report_view(self, report_type):
        view_class = self.testing_report_views.get(report_type, None)
        if view_class is None:
            return self.testing_report_views[None].as_view()
        else:
            return view_class.as_view()

    def get(self, request, *args, **kwargs):
        report_type = request.GET.get('report_type', None)
        view = self._get_testing_report_view(report_type)
        return view(request, *args, **kwargs)


class TestingReportCaseRuns(TestingReportBase, TestingReportCaseRunsData):
    template_name = 'report/caseruns.html'
    form_class = TestingReportCaseRunsListForm

    def get_context_data(self, **kwargs):
        data = super(TestingReportCaseRuns, self).get_context_data(**kwargs)

        query_args = self.request.GET
        form = self._get_form(query_args)

        if form.is_valid():
            test_case_runs = self.get_case_runs(form)
            status_names = TestCaseRunStatus.get_names()
            priority_values = dict(Priority.objects.values_list('pk', 'value'))

            testers_ids, assignees_ids = self._get_testers_assignees_ids(
                test_case_runs)
            testers = self.get_related_users(testers_ids)
            assignees = self.get_related_users(assignees_ids)

            data['test_case_runs_count'] = len(test_case_runs)
            data['test_case_runs'] = self.walk_case_runs(test_case_runs,
                                                         status_names,
                                                         priority_values,
                                                         testers,
                                                         assignees)
        else:
            data['form_errors'] = form.errors

        return data

    def _get_testers_assignees_ids(self, case_runs):
        testers_ids = set()
        assignees_ids = set()
        for case_run in case_runs:
            pk = case_run.tested_by_id
            if pk:
                testers_ids.add(case_run.tested_by_id)
            pk = case_run.assignee_id
            if pk:
                assignees_ids.add(case_run.assignee_id)
        return list(testers_ids), list(assignees_ids)

    def walk_case_runs(self, case_runs, status_names, priority_values,
                       testers, assignees):
        # todo: this is the same method as in testruns/views.py
        for case_run in case_runs:
            status_name = status_names[case_run.case_run_status_id]
            priority_value = priority_values[case_run.case.priority_id]
            tester_username = testers.get(case_run.tested_by_id, None)
            assignee_username = assignees.get(case_run.assignee_id, None)
            yield case_run, status_name, priority_value, (
                case_run.assignee_id, assignee_username), (
                    case_run.tested_by_id, tester_username)
