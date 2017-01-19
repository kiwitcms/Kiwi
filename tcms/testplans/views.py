# -*- coding: utf-8 -*-

import datetime
import itertools
import urllib

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.core import serializers
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404, \
    HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, render_to_response
from uuslug import slugify
from django.template import RequestContext
from django.template.loader import render_to_string
import json

from tcms.core.views import Prompt
from tcms.core.responses import HttpJSONResponse
from tcms.core.utils.raw_sql import RawSQL
from tcms.testcases.models import TestCase, TestCasePlan, TestCaseStatus, \
    TestCaseCategory
from tcms.management.models import TCMSEnvGroup, Component
from tcms.testplans.models import TestPlan, TestPlanComponent
from tcms.testruns.models import TestRun, TestCaseRun
from tcms.core.models import TCMSLog
from tcms.search.order import order_plan_queryset
from tcms.search import remove_from_request_path
from tcms.testcases.views import get_selected_testcases
from tcms.testplans.forms import NewPlanForm, EditPlanForm, ClonePlanForm, \
    ImportCasesViaXMLForm, SearchPlanForm, PlanComponentForm
from tcms.core.db import SQLExecution
from tcms.core.utils.checksum import checksum
from tcms.testcases.forms import SearchCaseForm, QuickSearchCaseForm
from tcms.testplans import sqls
from tcms.utils.dict_utils import create_group_by_dict as create_dict

MODULE_NAME = "testplans"


# _____________________________________________________________________________
# helper functons


def update_plan_email_settings(tp, form):
    '''Update testplan's email settings'''
    tp.emailing.notify_on_plan_update = form.cleaned_data[
        'notify_on_plan_update']
    tp.emailing.notify_on_plan_delete = form.cleaned_data[
        'notify_on_plan_delete']
    tp.emailing.notify_on_case_update = form.cleaned_data[
        'notify_on_case_update']
    tp.emailing.auto_to_plan_owner = form.cleaned_data['auto_to_plan_owner']
    tp.emailing.auto_to_plan_author = form.cleaned_data['auto_to_plan_author']
    tp.emailing.auto_to_case_owner = form.cleaned_data['auto_to_case_owner']
    tp.emailing.auto_to_case_default_tester = form.cleaned_data[
        'auto_to_case_default_tester']
    tp.emailing.save()


# _____________________________________________________________________________
# view functons


@user_passes_test(lambda u: u.has_perm('testplans.add_testplan'))
def new(request, template_name='plan/new.html'):
    '''New testplan'''
    SUB_MODULE_NAME = "new_plan"
    # If the form has been submitted...
    if request.method == 'POST':
        # A form bound to the POST data
        form = NewPlanForm(request.POST, request.FILES)
        form.populate(product_id=request.REQUEST.get('product'))

        # Process the upload plan document
        if form.is_valid():
            if form.cleaned_data.get('upload_plan_text'):
                # Set the summary form field to the uploaded text
                form.data['text'] = form.cleaned_data['text']

                # Generate the form
                context_data = {
                    'module': MODULE_NAME,
                    'sub_module': SUB_MODULE_NAME,
                    'form': form,
                }
                return render_to_response(template_name, context_data,
                                          context_instance=RequestContext(
                                              request))

        # Process the test plan submit to the form

        if form.is_valid():
            tp = TestPlan.objects.create(
                product=form.cleaned_data['product'],
                author=request.user,
                owner=request.user,
                product_version=form.cleaned_data['product_version'],
                type=form.cleaned_data['type'],
                name=form.cleaned_data['name'],
                create_date=datetime.datetime.now(),
                extra_link=form.cleaned_data['extra_link'],
                parent=form.cleaned_data['parent'],
            )

            # Add test plan text
            if request.user.has_perm('testplans.add_testplantext'):
                tp.add_text(
                    author=request.user,
                    plan_text=form.cleaned_data['text']
                )

            # Add test plan environment groups
            if request.user.has_perm('management.add_tcmsenvplanmap'):
                if request.REQUEST.get('env_group'):
                    env_groups = TCMSEnvGroup.objects.filter(
                        id__in=request.REQUEST.getlist('env_group')
                    )

                    for env_group in env_groups:
                        tp.add_env_group(env_group=env_group)

            return HttpResponseRedirect(
                reverse('tcms.testplans.views.get', args=[tp.plan_id, ])
            )
    else:
        form = NewPlanForm()

    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'form': form,
    }
    return render_to_response(template_name, context_data,
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('testplans.delete_testplan'))
def delete(request, plan_id):
    '''Delete testplan'''
    if request.GET.get('sure', 'no') == 'no':
        # TODO: rewrite the response
        return HttpResponse("\
            <script>if(confirm('Are you sure you want to delete this plan %s? \
            \\n \\n \
            Click OK to delete or cancel to come back')) { \
                window.location.href='%s?sure=yes' \
            } else { \
                history.go(-1) \
            };</script>" % (plan_id, reverse(
            'tcms.testplans.views.delete', args=[plan_id, ]
        ))
        )
    elif request.GET.get('sure') == 'yes':
        tp = get_object_or_404(TestPlan, plan_id=plan_id)

        try:
            tp.delete()
            return HttpResponse(
                "<script>window.location.href='%s'</script>" % reverse(
                    'tcms.testplans.views.all')
            )
        except:
            return HttpResponse(Prompt.render(
                request=request,
                info_type=Prompt.Info,
                info='Delete failed.',
                next='javascript:window.history.go(-1)',
            ))
    else:
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='Nothing yet.',
            next='javascript:window.history.go(-1)',
        ))


def all(request, template_name='plan/all.html'):
    '''Display all testplans'''
    # Define the default sub module
    SUB_MODULE_NAME = 'plans'
    # TODO: this function now only performs a forward feature, no queries
    # need here. All of it will be removed in the future.
    # If it's not a search the page will be blank
    tps = TestPlan.objects.none()
    query_result = False
    order_by = request.REQUEST.get('order_by', 'create_date')
    asc = bool(request.REQUEST.get('asc', None))
    # if it's a search request the page will be fill
    if request.REQUEST.items():
        search_form = SearchPlanForm(request.REQUEST)
        if request.REQUEST.get('product'):
            search_form.populate(product_id=request.REQUEST['product'])
        else:
            search_form.populate()

        if search_form.is_valid():
            # Detemine the query is the user's plans and change the sub
            # module value
            if request.REQUEST.get('author'):
                if request.user.is_authenticated():
                    if request.REQUEST['author'] == request.user.username \
                            or request.REQUEST['author'] == request.user.email:
                        SUB_MODULE_NAME = "my_plans"

            query_result = True
            # build a QuerySet:
            tps = TestPlan.list(search_form.cleaned_data)
            tps = tps.select_related('author', 'type', 'product')

            # We want to get the number of cases and runs, without doing
            # lots of per-test queries.
            #
            # Ideally we would get the case/run counts using m2m field tricks
            # in the ORM
            # Unfortunately, Django's select_related only works on ForeignKey
            # relationships, not on ManyToManyField attributes
            # See http://code.djangoproject.com/ticket/6432

            # SQLAlchemy can handle this kind of thing in several ways.
            # Unfortunately we're using Django

            # The cleanest way I can find to get it into one query is to
            # use QuerySet.extra()
            # See http://docs.djangoproject.com/en/dev/ref/models/querysets
            tps = tps.extra(select={
                'num_cases': RawSQL.num_cases,
                'num_runs': RawSQL.num_runs,
                'num_children': RawSQL.num_plans,
            })
            tps = order_plan_queryset(tps, order_by, asc)
    else:
        # Set search active plans only by default
        # I wish to use 'default' argument, as the same as in ModelForm
        # But it does not seem to work
        search_form = SearchPlanForm(initial={'is_active': True})

    if request.REQUEST.get('action') == 'clone_case':
        template_name = 'case/clone_select_plan.html'
        tps = tps.order_by('name')

    if request.REQUEST.get('t') == 'ajax':
        return HttpResponse(serializers.serialize(
            request.REQUEST.get('f', 'json'),
            tps,
            extras=('num_cases', 'num_runs', 'num_children', 'get_url_path')
        ))

    if request.REQUEST.get('t') == 'html':
        if request.REQUEST.get('f') == 'preview':
            template_name = 'plan/preview.html'

    query_url = remove_from_request_path(request, 'order_by')
    if asc:
        query_url = remove_from_request_path(query_url, 'asc')
    else:
        query_url = '%s&asc=True' % query_url
    page_type = request.REQUEST.get('page_type', 'pagination')
    query_url_page_type = remove_from_request_path(request, 'page_type')
    if query_url_page_type:
        query_url_page_type = remove_from_request_path(query_url_page_type,
                                                       'page')
    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_plans': tps,
        'query_result': query_result,
        'search_plan_form': search_form,
        'query_url': query_url,
        'query_url_page_type': query_url_page_type,
        'page_type': page_type
    }
    return render_to_response(template_name, context_data,
                              context_instance=RequestContext(request))


def get_number_of_plans_cases(plan_ids):
    '''Get the number of cases related to each plan

    Arguments:
    - plan_ids: a tuple or list of TestPlans' id

    Return value:
    Return value is an dict object, where key is plan_id and the value is the
    total count.
    '''
    qs = TestCasePlan.objects.filter(plan__in=plan_ids)
    qs = qs.values('plan').annotate(
        total_count=Count('pk')).order_by('-plan')
    return dict([(item['plan'], item['total_count']) for item in qs])


def get_number_of_plans_runs(plan_ids):
    '''Get the number of runs related to each plan

    Arguments:
    - plan_ids: a tuple or list of TestPlans' id

    Return value:
    Return value is an dict object, where key is plan_id and the value is the
    total count.
    '''
    qs = TestRun.objects.filter(plan__in=plan_ids)
    qs = qs.values('plan').annotate(
        total_count=Count('pk')).order_by('-plan')
    return dict([(item['plan'], item['total_count']) for item in qs])


def get_number_of_children_plans(plan_ids):
    '''Get the number of children plans related to each plan

    Arguments:
    - plan_ids: a tuple or list of TestPlans' id

    Return value:
    Return value is an dict object, where key is plan_id and the value is the
    total count.
    '''
    qs = TestPlan.objects.filter(parent__in=plan_ids)
    qs = qs.values('parent').annotate(
        total_count=Count('parent')).order_by('-parent')
    return dict([(item['parent'], item['total_count']) for item in qs])


def calculate_stats_for_testplans(plans):
    '''Attach the number of cases and runs for each TestPlan

    Arguments:
    - plans: the queryset of TestPlans

    Return value:
    A list of TestPlans, each of which is attached the statistics which is
    with prefix cal meaning calculation result.
    '''
    plan_ids = [plan.pk for plan in plans]
    cases_counts = get_number_of_plans_cases(plan_ids)
    runs_counts = get_number_of_plans_runs(plan_ids)
    children_counts = get_number_of_children_plans(plan_ids)

    # Attach calculated statistics to each object of TestPlan
    for plan in plans:
        setattr(plan, 'cal_cases_count', cases_counts.get(plan.pk, 0))
        setattr(plan, 'cal_runs_count', runs_counts.get(plan.pk, 0))
        setattr(plan, 'cal_children_count', children_counts.get(plan.pk, 0))

    return plans


def ajax_search(request, template_name='plan/common/json_plans.txt'):
    '''Display all testplans'''
    # Define the default sub module

    # If it's not a search the page will be blank
    tps = TestPlan.objects.none()
    # if it's a search request the page will be fill
    if request.REQUEST.items():
        search_form = SearchPlanForm(request.REQUEST)
        if request.REQUEST.get('product'):
            search_form.populate(product_id=request.REQUEST['product'])
        else:
            search_form.populate()
        if search_form.is_valid():
            # Detemine the query is the user's plans and change the sub
            # module value
            if request.REQUEST.get('author__email__startswith') and len(
                    search_form.changed_data) == 1:
                if request.user.is_authenticated():
                    if request.REQUEST[
                        'author__email__startswith'] == request.user.username \
                            or request.REQUEST[
                                'author__email__startswith'] == \
                            request.user.email:
                        user_email = request.REQUEST[
                            'author__email__startswith']
                        tps = TestPlan.objects.filter(
                            Q(author__email__startswith=user_email) |
                            Q(owner__email__startswith=user_email)). \
                            distinct()
            else:
                tps = TestPlan.list(search_form.cleaned_data)
                tps = tps.select_related('author', 'owner', 'type', 'product')
    # columnIndexNameMap is required for correct sorting behavior, 5 should
    # be product, but we use run.build.product
    columnIndexNameMap = {
        0: '',
        1: 'plan_id',
        2: 'name',
        3: 'author__username',
        4: 'owner__username',
        5: 'product',
        6: 'product_version',
        7: 'type',
        8: 'num_cases',
        9: 'num_runs',
        10: ''
    }
    return ajax_response(request, tps, columnIndexNameMap,
                         jsonTemplatePath='plan/common/json_plans.txt')


# TODO: refactor this method by moving sorting, pagination and data calculation
# to the outside. Response just does what the response is resposible for to the
# HTTP.
def ajax_response(request, querySet, columnIndexNameMap,
                  jsonTemplatePath='plan/common/json_plans.txt', *args):
    '''
    json template for the ajax request for searching.
    '''
    cols = int(request.GET.get('iColumns', 0))  # Get the number of columns
    # Safety measure. If someone messes with iDisplayLength manually, we
    # clip it to the max value of 100.
    iDisplayLength = min(int(request.GET.get('iDisplayLength', 20)), 100)
    if iDisplayLength == -1:
        startRecord = 0
        endRecord = querySet.count()
    else:
        # Where the data starts from (page)
        startRecord = int(request.GET.get('iDisplayStart', 0))
        # where the data ends (end of page)
        endRecord = startRecord + iDisplayLength
    # Pass sColumns
    keys = columnIndexNameMap.keys()
    keys.sort()
    colitems = [columnIndexNameMap[key] for key in keys]
    sColumns = ",".join(map(str, colitems))

    # Ordering data
    iSortingCols = int(request.GET.get('iSortingCols', 0))
    asortingCols = []

    if iSortingCols:
        for sortedColIndex in range(0, iSortingCols):
            sortedColID = int(
                request.GET.get('iSortCol_' + str(sortedColIndex), 0))
            # make sure the column is sortable first
            if request.GET.get('bSortable_%s' % sortedColID, 'false') == \
                    'true':
                sortedColName = columnIndexNameMap[sortedColID]
                sortingDirection = request.GET.get(
                    'sSortDir_' + str(sortedColIndex), 'asc')
                if sortingDirection == 'desc':
                    sortedColName = '-' + sortedColName
                asortingCols.append(sortedColName)
        if len(asortingCols):
            querySet = querySet.order_by(*asortingCols)
    # count how many records match the final criteria
    iTotalRecords = iTotalDisplayRecords = querySet.count()
    # get the slice
    querySet = querySet[startRecord:endRecord]

    # We need to display the number of cases and runs that are related to each
    # TestPlan.
    querySet = calculate_stats_for_testplans(querySet)

    sEcho = int(request.GET.get('sEcho', 0))  # required echo response

    if jsonTemplatePath:
        try:
            # prepare the JSON with the response, consider using :
            # from django.template.defaultfilters import escapejs
            jsonString = render_to_string(jsonTemplatePath, locals(),
                                          context_instance=RequestContext(
                                              request))
            response = HttpJSONResponse(jsonString)
        except Exception, e:
            print e
    else:
        aaData = []
        a = querySet.values()
        for row in a:
            rowkeys = row.keys()
            rowvalues = row.values()
            rowlist = []
            for col in range(0, len(colitems)):
                for idx, val in enumerate(rowkeys):
                    if val == colitems[col]:
                        rowlist.append(str(rowvalues[idx]))
            aaData.append(rowlist)
            response_dict = {}
            response_dict.update({'aaData': aaData})
            response_dict.update(
                {'sEcho': sEcho, 'iTotalRecords': iTotalRecords,
                 'iTotalDisplayRecords': iTotalDisplayRecords,
                 'sColumns': sColumns})
            response = HttpJSONResponse(json.dumps(response_dict))
            # prevent from caching datatables result
            # add_never_cache_headers(response)

    return response


def get(request, plan_id, slug=None, template_name='plan/get.html'):
    '''Display the plan details.'''
    SUB_MODULE_NAME = 'plans'

    try:
        tp = TestPlan.objects.select_related().get(plan_id=plan_id)
        tp.latest_text = tp.latest_text()
    except ObjectDoesNotExist:
        raise Http404

    # redirect if has a cheated slug
    if slug != slugify(tp.name):
        return HttpResponsePermanentRedirect(tp.get_absolute_url())

    # Initial the case counter
    confirm_status_name = 'CONFIRMED'
    tp.run_case = tp.case.filter(case_status__name=confirm_status_name)
    tp.review_case = tp.case.exclude(case_status__name=confirm_status_name)

    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_plan': tp,
        'xml_form': ImportCasesViaXMLForm(initial={'a': 'import_cases'}),
    }
    return render_to_response(template_name, context_data,
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('testruns.change_testrun'))
def choose_run(request, plan_id, template_name='plan/choose_testrun.html'):
    '''Choose one run to add cases'''

    # Define the default sub module
    SUB_MODULE_NAME = 'runs'
    if request.method == 'GET':
        try:
            plan_id = int(plan_id)
            tp = TestPlan.objects.filter(
                pk=plan_id).defer('product_version')[0]
        except:
            raise Http404

        testruns = TestRun.objects.filter(plan=plan_id).values(
            'pk', 'summary', 'build__name', 'manager__username')

        # Ready to write cases to test plan
        tcs = get_selected_testcases(request)
        tcs = tcs.values('pk', 'summary',
                         'author__username',
                         'create_date',
                         'category__name',
                         'priority__value', )

        context_data = {
            'module': MODULE_NAME,
            'sub_module': SUB_MODULE_NAME,
            'plan_id': plan_id,
            'plan': tp,
            'test_runs': testruns.iterator(),
            'test_cases': tcs.iterator(),
        }
        return render_to_response(template_name, context_data,
                                  context_instance=RequestContext(request))

    # Add cases to runs
    if request.method == 'POST':
        choosed_testrun_ids = request.REQUEST.getlist('testrun_ids')
        to_be_added_cases = TestCase.objects.filter(
            pk__in=request.REQUEST.getlist('case_ids'))

        # cases and runs are required in this process
        if not len(choosed_testrun_ids) or not len(to_be_added_cases):
            return HttpResponse(Prompt.render(
                request=request,
                info_type=Prompt.Info,
                info='At least one test run and one case is required to '
                     'add cases to runs.',
                next=reverse('tcms.testplans.views.get', args=[plan_id, ]),
            ))

        # Adding cases to runs by recursion
        for tr_id in choosed_testrun_ids:
            testrun = get_object_or_404(TestRun, run_id=tr_id)
            cases = TestCaseRun.objects.filter(run=tr_id)
            exist_cases_id = cases.values_list('case', flat=True)

            for testcase in to_be_added_cases:
                if testcase.case_id not in exist_cases_id:
                    testrun.add_case_run(case=testcase)

            estimated_time = reduce(lambda x, y: x + y,
                                    [nc.estimated_time for nc in
                                     to_be_added_cases])
            testrun.estimated_time = testrun.estimated_time + estimated_time
            testrun.save()

        return HttpResponseRedirect(
            reverse('tcms.testplans.views.get', args=[plan_id, ])
        )


@user_passes_test(lambda u: u.has_perm('testplans.change_testplan'))
def edit(request, plan_id, template_name='plan/edit.html'):
    '''Edit test plan view'''
    # Define the default sub module
    SUB_MODULE_NAME = 'plans'

    try:
        tp = TestPlan.objects.select_related().get(plan_id=plan_id)
    except ObjectDoesNotExist:
        raise Http404

    # If the form is submitted
    if request.method == "POST":
        form = EditPlanForm(request.POST, request.FILES)
        if request.REQUEST.get('product'):
            form.populate(product_id=request.REQUEST['product'])
        else:
            form.populate()

        # FIXME: Error handle
        if form.is_valid():
            if form.cleaned_data.get('upload_plan_text'):
                # Set the summary form field to the uploaded text
                form.data['text'] = form.cleaned_data['text']

                # Generate the form
                context_data = {
                    'module': MODULE_NAME,
                    'sub_module': SUB_MODULE_NAME,
                    'form': form,
                    'test_plan': tp,
                }
                return render_to_response(template_name, context_data,
                                          context_instance=RequestContext(
                                              request))

            if request.user.has_perm('testplans.change_testplan'):
                tp.name = form.cleaned_data['name']
                tp.parent = form.cleaned_data['parent']
                tp.product = form.cleaned_data['product']
                tp.product_version = form.cleaned_data['product_version']
                tp.type = form.cleaned_data['type']
                tp.is_active = form.cleaned_data['is_active']
                tp.extra_link = form.cleaned_data['extra_link']
                tp.owner = form.cleaned_data['owner']
                # IMPORTANT! tp.current_user is an instance attribute,
                # added so that in post_save, current logged-in user info
                # can be accessed.
                # Instance attribute is usually not a desirable solution.
                tp.current_user = request.user
                tp.save()

            if request.user.has_perm('testplans.add_testplantext'):
                new_text = request.REQUEST.get('text')
                text_checksum = checksum(new_text)

                if not tp.text_exist() or text_checksum != \
                        tp.text_checksum():
                    tp.add_text(
                        author=request.user,
                        plan_text=request.REQUEST.get('text'),
                        text_checksum=text_checksum
                    )

            if request.user.has_perm('management.change_tcmsenvplanmap'):
                tp.clear_env_groups()

                if request.REQUEST.get('env_group'):
                    env_groups = TCMSEnvGroup.objects.filter(
                        id__in=request.REQUEST.getlist('env_group')
                    )

                    for env_group in env_groups:
                        tp.add_env_group(env_group=env_group)
            # Update plan email settings
            update_plan_email_settings(tp, form)
            return HttpResponseRedirect(
                reverse('tcms.testplans.views.get',
                        args=[plan_id, slugify(tp.name)])
            )
    else:
        # Generate a blank form
        # Temporary use one environment group in this case
        if tp.env_group.all():
            for env_group in tp.env_group.all():
                env_group_id = env_group.id
                break
        else:
            env_group_id = None

        form = EditPlanForm(initial={
            'name': tp.name,
            'product': tp.product_id,
            'product_version': tp.product_version_id,
            'type': tp.type_id,
            'text': tp.latest_text() and tp.latest_text().plan_text or '',
            'parent': tp.parent_id,
            'env_group': env_group_id,
            'is_active': tp.is_active,
            'extra_link': tp.extra_link,
            'owner': tp.owner,
            'auto_to_plan_owner': tp.emailing.auto_to_plan_owner,
            'auto_to_plan_author': tp.emailing.auto_to_plan_author,
            'auto_to_case_owner': tp.emailing.auto_to_case_owner,
            'auto_to_case_default_tester':
            tp.emailing.auto_to_case_default_tester,
            'notify_on_plan_update': tp.emailing.notify_on_plan_update,
            'notify_on_case_update': tp.emailing.notify_on_case_update,
            'notify_on_plan_delete': tp.emailing.notify_on_plan_delete,
        })
        form.populate(product_id=tp.product_id)

    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_plan': tp,
        'form': form,
    }
    return render_to_response(template_name, context_data,
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('testplans.add_testplan'))
def clone(request, template_name='plan/clone.html'):
    '''Clone testplan'''
    SUB_MODULE_NAME = 'plans'

    if not request.REQUEST.get('plan'):
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='At least one plan is required by clone function.',
            next='javascript:window.history.go(-1)',
        ))

    tps = TestPlan.objects.filter(pk__in=request.REQUEST.getlist('plan'))

    if not tps:
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='The plan you specific does not exist in database',
            next='javascript:window.history.go(-1)',
        ))
    # Clone the plan if the form is submitted
    if request.method == "POST":
        clone_form = ClonePlanForm(request.REQUEST)
        clone_form.populate(product_id=request.REQUEST.get('product_id'))
        if clone_form.is_valid():

            # Create new test plan.
            for tp in tps:
                tp_dest = TestPlan.objects.create(
                    product=clone_form.cleaned_data['product'],
                    author=clone_form.cleaned_data['keep_orignal_author'] and
                    tp.author or request.user,
                    type=tp.type,
                    product_version=clone_form.cleaned_data['product_version'],
                    name=len(tps) == 1 and clone_form.cleaned_data[
                        'name'] or tp.name,
                    create_date=tp.create_date,
                    is_active=tp.is_active,
                    extra_link=tp.extra_link,
                    parent=clone_form.cleaned_data['set_parent'] and
                    tp or None,
                )

                # Copy the plan documents
                if clone_form.cleaned_data['copy_texts']:
                    tptxts_src = tp.text.all()
                    for tptxt_src in tptxts_src:
                        tp_dest.add_text(
                            plan_text_version=tptxt_src.plan_text_version,
                            author=tptxt_src.author,
                            create_date=tptxt_src.create_date,
                            plan_text=tptxt_src.plan_text,
                        )
                else:
                    tp_dest.add_text(author=request.user, plan_text='', )

                # Copy the plan tags
                for tp_tag_src in tp.tag.all():
                    tp_dest.add_tag(tag=tp_tag_src)

                # Copy the plan attachments
                if clone_form.cleaned_data['copy_attachements']:
                    for tp_attach_src in tp.attachment.all():
                        tp_dest.add_attachment(attachment=tp_attach_src)

                # Copy the environment group
                if clone_form.cleaned_data['copy_environment_group']:
                    for env_group in tp.env_group.all():
                        tp_dest.add_env_group(env_group=env_group)

                # Link the cases of the plan
                if clone_form.cleaned_data['link_testcases']:
                    tpcases_src = tp.case.all()

                    if clone_form.cleaned_data['copy_testcases']:
                        for tpcase_src in tpcases_src:
                            tcp = get_object_or_404(TestCasePlan, plan=tp,
                                                    case=tpcase_src)
                            if clone_form.cleaned_data[
                                    'maintain_case_orignal_author']:
                                author = tpcase_src.author
                            else:
                                author = request.user

                            if clone_form.cleaned_data[
                                    'keep_case_default_tester']:
                                if hasattr(tpcase_src, 'default_tester'):
                                    default_tester = getattr(tpcase_src,
                                                             'default_tester')
                                else:
                                    default_tester = None
                            else:
                                default_tester = request.user
                            tc_category, b_created = \
                                TestCaseCategory.objects.get_or_create(
                                    name=tpcase_src.category.name,
                                    product=clone_form.cleaned_data['product']
                                )
                            tpcase_dest = TestCase.objects.create(
                                create_date=tpcase_src.create_date,
                                is_automated=tpcase_src.is_automated,
                                script=tpcase_src.script,
                                arguments=tpcase_src.arguments,
                                summary=tpcase_src.summary,
                                requirement=tpcase_src.requirement,
                                alias=tpcase_src.alias,
                                estimated_time=tpcase_src.estimated_time,
                                case_status=TestCaseStatus.get_PROPOSED(),
                                category=tc_category,
                                priority=tpcase_src.priority,
                                author=author,
                                default_tester=default_tester,
                            )

                            # Add case to plan.
                            tp_dest.add_case(tpcase_dest, tcp.sortkey)

                            for tc_tag_src in tpcase_src.tag.all():
                                tpcase_dest.add_tag(tag=tc_tag_src)
                            for component in tpcase_src.component.filter(
                                    product__id=tp.product_id):
                                try:
                                    new_c = tp_dest.product.component.get(
                                        name=component.name
                                    )
                                except ObjectDoesNotExist:
                                    new_c = tp_dest.product.component.create(
                                        name=component.name,
                                        initial_owner=request.user,
                                        description=component.description,
                                    )

                                tpcase_dest.add_component(new_c)

                            text = tpcase_src.latest_text()

                            if text:
                                tpcase_dest.add_text(
                                    author=text.author,
                                    action=text.action,
                                    effect=text.effect,
                                    setup=text.setup,
                                    breakdown=text.breakdown,
                                    create_date=text.create_date,
                                )

                    else:
                        for tpcase_src in tpcases_src:
                            tcp = get_object_or_404(TestCasePlan, plan=tp,
                                                    case=tpcase_src)
                            tp_dest.add_case(tpcase_src, tcp.sortkey)

            if len(tps) == 1:
                return HttpResponseRedirect(
                    reverse('tcms.testplans.views.get',
                            args=[tp_dest.plan_id, ])
                )
            else:
                args = {
                    'action': 'search',
                    'product': clone_form.cleaned_data['product'].id,
                    'product_version': clone_form.cleaned_data[
                        'product_version'].id
                }

                url_args = urllib.urlencode(args)

                return HttpResponseRedirect(
                    reverse('tcms.testplans.views.all') + '?' + url_args
                )
    else:
        # Generate the default values for the form
        if len(tps) == 1:
            clone_form = ClonePlanForm(initial={
                'product': tps[0].product_id,
                'product_version': tps[0].product_version_id,
                'set_parent': True,
                'copy_texts': True,
                'copy_attachements': True,
                'copy_environment_group': True,
                'link_testcases': True,
                'copy_testcases': False,
                'maintain_case_orignal_author': True,
                'keep_case_default_tester': False,
                'name': 'Copy of %s' % tps[0].name
            })
            clone_form.populate(product_id=tps[0].product.id)
        else:
            clone_form = ClonePlanForm(initial={
                'set_parent': True,
                'copy_texts': True,
                'copy_attachements': True,
                'link_testcases': True,
                'copy_testcases': False,
                'maintain_case_orignal_author': True,
                'keep_case_default_tester': True,
            })

    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'testplans': tps,
        'clone_form': clone_form,
    }
    return render_to_response(template_name, context_data,
                              context_instance=RequestContext(request))


def attachment(request, plan_id, template_name='plan/attachment.html'):
    '''Manage attached files'''
    SUB_MODULE_NAME = 'plans'

    file_size_limit = settings.MAX_UPLOAD_SIZE
    limit_readable = int(file_size_limit) / 2 ** 20  # Mb

    tp = get_object_or_404(TestPlan, plan_id=plan_id)
    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_plan': tp,
        'limit': file_size_limit,
        'limit_readable': str(limit_readable) + "Mb",
    }
    return render_to_response(template_name, context_data,
                              context_instance=RequestContext(request))


def text_history(request, plan_id, template_name='plan/history.html'):
    '''View test plan text history'''
    SUB_MODULE_NAME = 'plans'

    tp = get_object_or_404(TestPlan, plan_id=plan_id)
    tptxts = tp.text.all()
    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'testplan': tp,
        'test_plan_texts': tptxts,
        'select_plan_text_version': int(
            request.REQUEST.get('plan_text_version', 0)
        ),
    }
    return render_to_response(template_name, context_data,
                              context_instance=RequestContext(request))


def cases(request, plan_id):
    '''Process the xml with import'''
    ajax_response = {'rc': 0, 'response': 'ok'}
    tp = get_object_or_404(TestPlan, plan_id=plan_id)

    class CaseActions(object):
        def __init__(self, request, tp):
            self.__all__ = ['link_cases',
                            'delete_cases',
                            'order_cases',
                            'import_cases']
            self.request = request
            self.tp = tp

        def link_cases(self, template_name='plan/search_case.html'):
            '''
            Handle to form to add case to plans.
            '''
            SUB_MODULE_NAME = 'plans'
            tcs = None

            if request.REQUEST.get('action') == 'add_to_plan':
                if request.user.has_perm('testcases.add_testcaseplan'):
                    tcs = TestCase.objects.filter(
                        case_id__in=request.REQUEST.getlist('case'))

                    for tc in tcs:
                        tp.add_case(tc)
                else:
                    return HttpResponse("Permission Denied")

                return HttpResponseRedirect(
                    reverse('tcms.testplans.views.get', args=[plan_id, ])
                )

            search_mode = request.REQUEST.get('search_mode')
            if request.REQUEST.get('action') == 'search':

                if search_mode == 'quick':
                    form = quick_form = QuickSearchCaseForm(request.REQUEST)
                    normal_form = SearchCaseForm()
                else:
                    form = normal_form = SearchCaseForm(request.REQUEST)
                    form.populate(product_id=request.REQUEST.get('product'))
                    quick_form = QuickSearchCaseForm()

                if form.is_valid():
                    tcs = TestCase.list(form.cleaned_data)
                    tcs = tcs.select_related(
                        'author', 'default_tester', 'case_status',
                        'priority', 'category', 'tag__name'
                    ).only('pk', 'summary', 'create_date',
                           'author__email', 'default_tester__email',
                           'case_status__name', 'priority__value',
                           'category__name', 'tag__name')
                    tcs = tcs.exclude(case_id__in=tp.case.values_list(
                        'case_id', flat=True
                    ))
            else:
                normal_form = SearchCaseForm(initial={
                    'product': tp.product_id,
                    'product_version': tp.product_version_id,
                    'case_status_id': TestCaseStatus.get_CONFIRMED()
                })
                quick_form = QuickSearchCaseForm()

            context_data = {
                'module': MODULE_NAME,
                'sub_module': SUB_MODULE_NAME,
                'test_plan': tp,
                'test_cases': tcs,
                'search_form': normal_form,
                'quick_form': quick_form,
                'search_mode': search_mode
            }
            return render_to_response(template_name, context_data,
                                      context_instance=RequestContext(request))

        def delete_cases(self):
            if not request.REQUEST.get('case'):
                ajax_response['rc'] = 1
                ajax_response[
                    'reponse'] = 'At least one case is required to delete.'
                return HttpResponse(json.dumps(ajax_response))

            tcs = get_selected_testcases(request)

            # Log Action
            tp_log = TCMSLog(model=tp)

            for tc in tcs:
                tp_log.make(
                    who=request.user,
                    action='Remove case %s from plan %s' % (
                        tc.case_id, tp.plan_id)
                )

                tc.log_action(
                    who=request.user,
                    action='Remove from plan %s' % tp.plan_id
                )

                tp.delete_case(case=tc)

            return HttpResponse(json.dumps(ajax_response))

        def order_cases(self):
            '''
            Resort case with new order
            '''
            # Current we should rewrite all of cases belong to the plan.
            # Because the cases sortkey in database is chaos,
            # Most of them are None.

            if not request.REQUEST.get('case'):
                ajax_response['rc'] = 1
                ajax_response[
                    'reponse'] = 'At least one case is required to re-order.'
                return HttpResponse(json.dumps(ajax_response))

            tc_pks = request.REQUEST.getlist('case')
            tcs = TestCase.objects.filter(pk__in=tc_pks)

            for tc in tcs:
                new_sort_key = (tc_pks.index(str(tc.pk)) + 1) * 10
                TestCasePlan.objects.filter(plan=tp, case=tc).update(
                    sortkey=new_sort_key)

            return HttpResponse(json.dumps(ajax_response))

        def import_cases(self):

            if request.method == 'POST':
                # Process import case from XML action
                if not request.user.has_perm('testcases.add_testcaseplan'):
                    return HttpResponse(Prompt.render(
                        request=request,
                        info_type=Prompt.Alert,
                        info='Permission denied',
                        next=reverse('tcms.testplans.views.get',
                                     args=[plan_id, ]),
                    ))

                xml_form = ImportCasesViaXMLForm(request.REQUEST,
                                                 request.FILES)

                if xml_form.is_valid():
                    i = 0
                    for case in xml_form.cleaned_data['xml_file']:
                        i += 1

                        # Get the case category from the case and related to
                        # the product of the plan
                        try:
                            category = TestCaseCategory.objects.get(
                                product=tp.product, name=case['category_name']
                            )
                        except TestCaseCategory.DoesNotExist:
                            category = TestCaseCategory.objects.create(
                                product=tp.product, name=case['category_name']
                            )

                        # Start to create the objects
                        tc = TestCase.objects.create(
                            is_automated=case['is_automated'],
                            script=None,
                            arguments=None,
                            summary=case['summary'],
                            requirement=None,
                            alias=None,
                            estimated_time=0,
                            case_status_id=case['case_status_id'],
                            category_id=category.id,
                            priority_id=case['priority_id'],
                            author_id=case['author_id'],
                            default_tester_id=case['default_tester_id'],
                            notes=case['notes'],
                        )
                        TestCasePlan.objects.create(plan=tp, case=tc,
                                                    sortkey=i * 10)

                        tc.add_text(case_text_version=1,
                                    author=case['author'],
                                    action=case['action'],
                                    effect=case['effect'],
                                    setup=case['setup'],
                                    breakdown=case['breakdown'], )

                        # handle tags
                        if case['tags']:
                            for tag in case['tags']:
                                tc.add_tag(tag=tag)

                        tc.add_to_plan(plan=tp)

                    return HttpResponseRedirect(
                        reverse('tcms.testplans.views.get',
                                args=[plan_id, ]) + '#testcases')
                else:
                    return HttpResponse(Prompt.render(
                        request=request,
                        info_type=Prompt.Alert,
                        info=xml_form.errors,
                        next=reverse('tcms.testplans.views.get',
                                     args=[plan_id, ]) + '#testcases'
                    ))
            else:
                return HttpResponseRedirect(reverse('tcms.testplans.views.get',
                                                    args=[plan_id, ]) +
                                            '#testcases')

    # tp = get_object_or_404(TestPlan, plan_id=plan_id)
    cas = CaseActions(request, tp)
    actions = request.REQUEST.get('a')

    if actions not in cas.__all__:
        if request.REQUEST.get('format') == 'json':
            ajax_response['rc'] = 1
            ajax_response['response'] = 'Unrecognizable actions'
            return HttpResponse(json.dumps(ajax_response))

        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Alert,
            info='Unrecognizable actions',
            next=reverse('tcms.testplans.views.get', args=[plan_id, ]),
        ))

    func = getattr(cas, actions)
    return func()


def component(request, template_name='plan/get_component.html'):
    '''Manage the component template for plan

    Parameters:
      plan - Necessary, to determine which plan you need to modify the
             component template
      a - Optional, Actions for the plan, now it have 'add', 'remove', 'update'
          and 'render' actions. 'render' is default, use for render the page.
          'update' is use for clean the components then add the new components
          you specific.
      component - Optional, The component ID you wish to operate.
      multiple - Optional, When you modify multiple, the parameter need to
                 post. It will response a JSON not a page.

    Returns:
      HTML page by default, or a JSON when the 'multiple' parameter specific.
    '''
    ajax_response = {'rc': 0, 'response': 'ok'}

    class ComponentActions(object):
        def __init__(self, request, tps, cs):
            self.__all__ = ['add', 'clear', 'get_form', 'remove', 'update',
                            'render']
            self.__msgs__ = {
                'permission_denied': {'rc': 1, 'response': 'Permisson denied'},
            }

            self.request = request
            self.tps = tps
            self.cs = cs

        def add(self):
            if not self.request.user.has_perm(
                    'testplans.add_testplancomponent'):
                if self.is_ajax():
                    return HttpResponse(
                        json.dumps(self.__msgs__['permission_denied']))

                return self.render(
                    message=self.__msgs__['permission_denied']['response'])

            for tp in self.tps:
                for c in cs:
                    tp.add_component(c)
            return self.render()

        def clear(self):
            if not self.request.user.has_perm(
                    'testplans.delete_testplancomponent'):
                pass

            # Remove the exist components
            TestPlanComponent.objects.filter(
                plan__in=self.tps,
            ).delete()

        def get_form(self):
            tpcs = TestPlanComponent.objects.filter(plan=self.tps)

            form = PlanComponentForm(tps=self.tps, initial={
                'component': tpcs.values_list('component_id', flat=True),
            })

            q_format = request.REQUEST.get('format')
            if not q_format:
                q_format = 'p'
            html = getattr(form, 'as_' + q_format)

            return HttpResponse(html())

        def remove(self):
            if not self.request.user.has_perm(
                    'testplans.delete_testplancomponent'):
                if self.request.is_ajax():
                    return HttpResponse(
                        json.dumps(self.__msgs__['permission_denied']))

                return self.render(
                    message=self.__msgs__['permission_denied']['response'])

            for tp in self.tps:
                for c in cs:
                    tp.remove_component(c)

            return self.render()

        def update(self):
            self.clear()
            self.add()
            return self.render()

        def render(self, message=None):
            if request.REQUEST.get('multiple'):
                return HttpResponse(json.dumps(ajax_response))

            if request.REQUEST.get('type'):
                from django.core import serializers

                obj = TestPlanComponent.objects.filter(
                    plan__in=self.tps,
                )

                return HttpResponse(
                    serializers.serialize(request.REQUEST['type'], obj)
                )

            context_data = {
                'test_plan': self.tps[0],
            }
            return render_to_response(template_name, context_data,
                                      context_instance=RequestContext(request))

    if not request.REQUEST.get('plan'):
        raise Http404

    tps = TestPlan.objects.filter(pk__in=request.REQUEST.getlist('plan'))

    if request.REQUEST.get('component'):
        cs = Component.objects.filter(
            pk__in=request.REQUEST.getlist('component'))
    else:
        cs = Component.objects.none()

    cas = ComponentActions(request=request, tps=tps, cs=cs)

    action = getattr(cas, request.REQUEST.get('a', 'render').lower())
    return action()


def tree_view(request):
    '''Whole tree view for plans'''
    # FIXME:


def printable(request, template_name='plan/printable.html'):
    '''Create the printable copy for plan'''
    req_getlist = request.REQUEST.getlist

    plan_pks = req_getlist('plan')

    if not plan_pks:
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='At least one target is required.', ))

    tps = TestPlan.objects.filter(pk__in=plan_pks).only('pk', 'name')

    def plan_generator():
        repeat = len(plan_pks)
        params_sql = ','.join(itertools.repeat('%s', repeat))
        sql = sqls.TP_PRINTABLE_CASE_TEXTS % (params_sql, params_sql)
        result_set = SQLExecution(sql, plan_pks * 2)
        group_data = itertools.groupby(result_set.rows,
                                       lambda data: data['plan_id'])
        cases_dict = dict((key, list(values)) for key, values in group_data)
        for tp in tps:
            tp.result_set = cases_dict.get(tp.plan_id, None)

            yield tp

    context_data = {
        'test_plans': plan_generator(),
    }

    return render_to_response(template_name, context_data,
                              context_instance=RequestContext(request))


def export(request, template_name='plan/export.xml'):
    '''Export the plan'''
    plan_pks = request.REQUEST.getlist('plan')
    if not plan_pks:
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='At least one target is required.', ))
    timestamp = datetime.datetime.now()
    timestamp_str = '%02i-%02i-%02i' \
                    % (timestamp.year, timestamp.month, timestamp.day)

    context_data = {
        'data_generator': generator_proxy(plan_pks),
    }

    response = render_to_response(template_name, context_data,
                                  context_instance=RequestContext(request))
    response['Content-Disposition'] = \
        'attachment; filename=tcms-testcases-%s.xml' % timestamp_str
    return response


def generator_proxy(plan_pks):
    def key_func(data):
        return (data['plan_id'], data['case_id'])

    params_sql = ','.join(itertools.repeat('%s', len(plan_pks)))
    metas = SQLExecution(sqls.TP_EXPORT_ALL_CASES_META % params_sql,
                         plan_pks).rows
    compoment_dict = create_dict(
        sqls.TP_EXPORT_ALL_CASES_COMPONENTS % params_sql,
        plan_pks,
        key_func)
    tag_dict = create_dict(sqls.TP_EXPORT_ALL_CASE_TAGS % params_sql,
                           plan_pks,
                           key_func)

    sql = sqls.TP_EXPORT_ALL_CASE_TEXTS % (params_sql, params_sql)
    plan_text_dict = create_dict(sql, plan_pks * 2, key_func)

    for meta in metas:
        plan_id = meta['plan_id']
        case_id = meta['case_id']
        c_meta = compoment_dict.get((plan_id, case_id), None)
        if c_meta:
            meta['c_meta'] = c_meta

        tag = tag_dict.get((plan_id, case_id), None)
        if tag:
            meta['tag'] = tag

        plan_text = plan_text_dict.get((plan_id, case_id), None)
        if plan_text:
            meta['latest_text'] = plan_text

        yield meta
