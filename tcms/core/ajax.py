# -*- coding: utf-8 -*-
"""
Shared functions for plan/case/run.

Most of these functions are use for Ajax.
"""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View

from tcms.testcases.models import TestCase


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
