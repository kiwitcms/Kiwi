# -*- coding: utf-8 -*-
"""
Shared functions for plan/case/run.

Most of these functions are use for Ajax.
"""
from http import HTTPStatus
from distutils.util import strtobool

from django.db.models import Count
from django.contrib.auth.models import User
from django.core import serializers
from django.forms import ValidationError
from django.http import HttpResponse, JsonResponse
from django.views.generic.base import View
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import permission_required

from tcms.management.models import Component, Build, Version
from tcms.management.models import Tag
from tcms.management.models import EnvGroup, EnvProperty, EnvValue
from tcms.testcases.models import TestCase, Bug
from tcms.testcases.models import Category
from tcms.testcases.models import TestCaseTag
from tcms.testplans.models import TestPlan, TestPlanTag
from tcms.testruns.models import TestRun, TestCaseRun, TestRunTag
from tcms.core.helpers.comments import add_comment
from tcms.core.utils.validations import validate_bug_id


@require_GET
def info(request):
    """Ajax responder for misc information"""

    objects = _InfoObjects(request=request, product_id=request.GET.get('product_id'))
    info_type = getattr(objects, request.GET.get('info_type'))

    if not info_type:
        return HttpResponse('Unrecognizable info-type')

    return HttpResponse(serializers.serialize('json', info_type(), fields=('name', 'value')))


class _InfoObjects(object):

    def __init__(self, request, product_id=None):
        self.request = request
        try:
            self.product_id = int(product_id)
        except (ValueError, TypeError):
            self.product_id = 0

    def builds(self):
        try:
            is_active = strtobool(self.request.GET.get('is_active', default='False'))
        except (ValueError, TypeError):
            is_active = False

        return Build.objects.filter(product_id=self.product_id, is_active=is_active)

    def categories(self):
        return Category.objects.filter(product__id=self.product_id)

    def components(self):
        return Component.objects.filter(product__id=self.product_id)

    def env_properties(self):
        if self.request.GET.get('env_group_id'):
            return EnvGroup.objects.get(id=self.request.GET['env_group_id']).property.all()
        return EnvProperty.objects.all()

    def env_values(self):
        return EnvValue.objects.filter(property__id=self.request.GET.get('env_property_id'))

    def tags(self):
        return Tag.objects.filter(name__startswith=self.request.GET['name__startswith'])

    def versions(self):
        return Version.objects.filter(product__id=self.product_id)

    @staticmethod
    def env_groups():
        return EnvGroup.objects.all()


def tags(request):
    """ Get tags for TestPlan, TestCase or TestRun """

    tag_objects = _TagObjects(request)
    template_name, obj = tag_objects.get()

    q_tag = request.GET.get('tags')
    q_action = request.GET.get('a')

    if q_action:
        tag_actions = _TagActions(obj=obj, tag_name=q_tag)
        getattr(tag_actions, q_action)()

    all_tags = obj.tag.all().order_by('pk')
    test_plan_tags = TestPlanTag.objects.filter(
        tag__in=all_tags).values('tag').annotate(num_plans=Count('tag')).order_by('tag')
    test_case_tags = TestCaseTag.objects.filter(
        tag__in=all_tags).values('tag').annotate(num_cases=Count('tag')).order_by('tag')
    test_run_tags = TestRunTag.objects.filter(
        tag__in=all_tags).values('tag').annotate(num_runs=Count('tag')).order_by('tag')

    plan_counter = _TagCounter('num_plans', test_plan_tags)
    case_counter = _TagCounter('num_cases', test_case_tags)
    run_counter = _TagCounter('num_runs', test_run_tags)

    for tag in all_tags:
        tag.num_plans = plan_counter.calculate_tag_count(tag)
        tag.num_cases = case_counter.calculate_tag_count(tag)
        tag.num_runs = run_counter.calculate_tag_count(tag)

    context_data = {
        'tags': all_tags,
        'object': obj,
    }
    return render(request, template_name, context_data)


class _TagObjects(object):
    """ Used for getting the chosen object(TestPlan, TestCase or TestRun) from the database """

    def __init__(self, request):
        """
        :param request: An HTTP GET request, containing the primary key
                        and the type of object to be selected
        :type request: HttpRequest
        """
        for obj in ['plan', 'case', 'run']:
            if request.GET.get(obj):
                self.object = obj
                self.object_pk = request.GET.get(obj)
                break

    def get(self):
        func = getattr(self, self.object)
        return func()

    def plan(self):
        return 'management/get_tag.html', TestPlan.objects.get(pk=self.object_pk)

    def case(self):
        return 'management/get_tag.html', TestCase.objects.get(pk=self.object_pk)

    def run(self):
        return 'run/get_tag.html', TestRun.objects.get(pk=self.object_pk)


class _TagActions(object):
    """ Used for performing the 'add' and 'remove' actions on a given tag """

    def __init__(self, obj, tag_name):
        """
        :param obj: the object for which the tag actions would be performed
        :type obj: either a :class:`tcms.testplans.models.TestPlan`,
                          a :class:`tcms.testcases.models.TestCase` or
                          a :class:`tcms.testruns.models.TestRun`
        :param tag_name: The name of the tag to be manipulated
        :type tag_name: str
        """
        self.obj = obj
        self.tag_name = tag_name

    def add(self):
        tag, _ = Tag.objects.get_or_create(name=self.tag_name)
        self.obj.add_tag(tag)

    def remove(self):
        tag = Tag.objects.get(name=self.tag_name)
        self.obj.remove_tag(tag)


class _TagCounter(object):  # pylint: disable=too-few-public-methods
    """ Used for counting the number of times a tag is assigned to TestRun/TestCase/TestPlan """

    def __init__(self, key, test_tags):
        """
         :param key: either 'num_plans', 'num_cases', 'num_runs', depending on what you want count
         :type key: str
         :param test_tags: query set, containing the Tag->Object relationship, ordered by tag and
                            annotated by key
            e.g. TestPlanTag, TestCaseTag ot TestRunTag
         :type test_tags: QuerySet
        """
        self.key = key
        self.test_tags = iter(test_tags)
        self.counter = {'tag': 0}

    def calculate_tag_count(self, tag):
        """
        :param tag: the tag you do the counting for
        :type tag: :class:`tcms.management.models.Tag`
        :return: the number of times a tag is assigned to object
        :rtype: int
        """
        if self.counter['tag'] != tag.pk:
            try:
                self.counter = self.test_tags.__next__()
            except StopIteration:
                return 0

        if tag.pk == self.counter['tag']:
            return self.counter[self.key]
        return 0


def say_no(error_msg):
    return JsonResponse({'rc': 1, 'response': error_msg})


def say_yes():
    return JsonResponse({'rc': 0, 'response': 'ok'})


@method_decorator(permission_required('testcases.change_testcase'), name='dispatch')
class UpdateTestCaseStatusView(View):
    """Updates TestCase.case_status_id. Called from the front-end."""

    http_method_names = ['post']

    def post(self, request):
        status_id = int(request.POST.get('new_value'))
        case_ids = request.POST.getlist('case[]')

        for test_case in TestCase.objects.filter(pk__in=case_ids):
            test_case.case_status_id = status_id
            test_case.save()

        # Case is moved between Cases and Reviewing Cases tabs accoding to the
        # change of status. Meanwhile, the number of cases with each status
        # should be updated also.
        plan_id = request.POST.get("from_plan")
        test_plan = get_object_or_404(TestPlan, pk=plan_id)

        confirmed_cases_count = test_plan.case.filter(case_status__name='CONFIRMED').count()
        total_cases_count = test_plan.case.count()
        review_cases_count = total_cases_count - confirmed_cases_count

        return JsonResponse({
            'rc': 0,
            'response': 'ok',
            'run_case_count': confirmed_cases_count,
            'case_count': total_cases_count,
            'review_case_count': review_cases_count,
        })


@method_decorator(permission_required('testcases.change_testcase'), name='dispatch')
class UpdateTestCasePriorityView(View):
    """Updates TestCase.priority_id. Called from the front-end."""

    http_method_names = ['post']

    def post(self, request):
        priority_id = int(request.POST.get('new_value'))
        case_ids = request.POST.getlist('case[]')

        for test_case in TestCase.objects.filter(pk__in=case_ids):
            test_case.priority_id = priority_id
            test_case.save()

        return JsonResponse({'rc': 0, 'response': 'ok'})


@method_decorator(permission_required('testcases.change_testcase'), name='dispatch')
class UpdateTestCaseActorsView(View):
    """
        Updates TestCase.default_tester_id or TestCase.reviewer_id.
        Called from the front-end.
    """

    http_method_names = ['post']

    def post(self, request):
        username = request.POST.get('username')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return JsonResponse({'rc': 1,
                                     'response': _('User %s not found!' % username)},
                                    status=HTTPStatus.NOT_FOUND)

        what_to_update = request.POST.get('what_to_update')
        case_ids = request.POST.getlist('case[]')
        for test_case in TestCase.objects.filter(pk__in=case_ids):
            if what_to_update == 'default_tester':
                test_case.default_tester_id = user.pk
            elif what_to_update == 'reviewer':
                test_case.reviewer_id = user.pk

            test_case.save()

        return JsonResponse({'rc': 0, 'response': 'ok'})


@require_POST
def comment_case_runs(request):
    """
    Add comment to one or more caseruns at a time.
    """
    data = request.POST.copy()
    comment = data.get('comment', None)
    if not comment:
        return say_no('Comments needed')
    run_ids = [i for i in data.get('run', '').split(',') if i]
    if not run_ids:
        return say_no('No runs selected.')
    runs = TestCaseRun.objects.filter(pk__in=run_ids).only('pk')
    if not runs:
        return say_no('No caserun found.')
    add_comment(runs, comment, request.user)
    return say_yes()


def clean_bug_form(request):
    """
    Verify the form data, return a tuple\n
    (None, ERROR_MSG) on failure\n
    or\n
    (data_dict, '') on success.\n
    """
    data = {}
    try:
        data['bugs'] = request.GET.get('bug_id', '').split(',')
        data['runs'] = map(int, request.GET.get('case_runs', '').split(','))
    except (TypeError, ValueError) as error:
        return (None, 'Please specify only integers for bugs, '
                      'caseruns(using comma to seperate IDs), '
                      'and bug_system. (DEBUG INFO: %s)' % str(error))

    data['bug_system_id'] = int(request.GET.get('bug_system_id', 1))

    if request.GET.get('a') not in ('add', 'remove'):
        return (None, 'Actions only allow "add" and "remove".')
    else:
        data['action'] = request.GET.get('a')
    data['bz_external_track'] = True if request.GET.get('bz_external_track',
                                                        False) else False

    return (data, '')


def update_bugs_to_caseruns(request):
    """
    Add one or more bugs to or remove that from\n
    one or more caserun at a time.
    """
    data, error = clean_bug_form(request)
    if error:
        return say_no(error)
    runs = TestCaseRun.objects.filter(pk__in=data['runs'])
    bug_system_id = data['bug_system_id']
    bug_ids = data['bugs']

    try:
        validate_bug_id(bug_ids, bug_system_id)
    except ValidationError as error:
        return say_no(str(error))

    bz_external_track = data['bz_external_track']
    action = data['action']
    try:
        if action == "add":
            for run in runs:
                for bug_id in bug_ids:
                    run.add_bug(bug_id=bug_id,
                                bug_system_id=bug_system_id,
                                bz_external_track=bz_external_track)
        else:
            bugs = Bug.objects.filter(bug_id__in=bug_ids)
            for run in runs:
                for bug in bugs:
                    if bug.case_run_id == run.pk:
                        run.remove_bug(bug.bug_id, run.pk)
    except Exception as error:
        return say_no(str(error))
    return say_yes()


def get_prod_related_objs(p_pks, target):
    """
    Get Component, Version, Category, and Build\n
    Return [(id, name), (id, name)]
    """
    ctypes = {
        'component': (Component, 'name'),
        'version': (Version, 'value'),
        'build': (Build, 'name'),
        'category': (Category, 'name'),
    }
    results = ctypes[target][0]._default_manager.filter(product__in=p_pks)
    attr = ctypes[target][1]
    results = [(r.pk, getattr(r, attr)) for r in results]
    return results


def get_prod_related_obj_json(request):
    """
    View for updating product drop-down\n
    in a Ajax way.
    """
    data = request.GET.copy()
    target = data.get('target', None)
    p_pks = data.get('p_ids', None)
    sep = data.get('sep', None)
    # py2.6: all(*values) => boolean ANDs
    if target and p_pks and sep:
        p_pks = [k for k in p_pks.split(sep) if k]
        res = get_prod_related_objs(p_pks, target)
    else:
        res = []
    return JsonResponse(res)
