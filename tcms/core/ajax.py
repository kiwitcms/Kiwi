# -*- coding: utf-8 -*-
"""
Shared functions for plan/case/run.

Most of these functions are use for Ajax.
"""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View

from tcms.testcases.models import TestCase, TestCaseTag
from tcms.testplans.models import TestPlan, TestPlanTag
from tcms.testruns.models import TestRunTag


def tags(request):
    """
        Get tags for TestPlan or TestCase.
        Also counts how many times the same tag has been used for
        different objects. Used in TP -> Tags and TC -> Tags tabs!
    """

    template_name, obj = _TagObjects(request).get()

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

    api_module = 'NotExisting'
    if isinstance(obj, TestPlan):
        api_module = 'TestPlan'

    if isinstance(obj, TestCase):
        api_module = 'TestCase'

    context_data = {
        'tags': all_tags,
        'object': obj,
        'api_module': api_module,
    }
    # todo: convert this method into returning pure JSON and
    # render inside the browser. Also move it under management.views
    return render(request, template_name, context_data)


class _TagObjects:
    """ Used for getting the chosen object(TestPlan, TestCase or TestRun) from the database """

    def __init__(self, request):
        """
        :param request: An HTTP GET request, containing the primary key
                        and the type of object to be selected
        :type request: HttpRequest
        """
        for obj in ['plan', 'case']:
            if request.GET.get(obj):
                self.object = obj
                self.object_pk = request.GET.get(obj)
                break

    def get(self):
        func = getattr(self, self.object)
        return func()

    def plan(self):
        return 'management/get_tag.html', TestPlan.objects.get(pk=self.object_pk)


class _TagCounter:  # pylint: disable=too-few-public-methods
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
class UpdateTestCaseActorsView(View):
    """
        Updates TestCase.default_tester_id or TestCase.reviewer_id.
        Called from the front-end.
    """

    http_method_names = ['post']

    def post(self, request):
        username = request.POST.get('username')
        User = get_user_model()  # pylint: disable=invalid-name
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return JsonResponse({'rc': 1,
                                     'response': _('User %s not found!') % username},
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
