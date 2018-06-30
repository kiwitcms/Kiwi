# -*- coding: utf-8 -*-

from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestRun
from tcms.profiles.models import Bookmark
from tcms.profiles.models import UserProfile
from tcms.profiles.forms import BookmarkForm, UserProfileForm


@require_http_methods(['GET', 'POST'])
@login_required
def bookmarks(request):
    """
    Bookmarks for the user
    """
    class BookmarkActions(object):
        def __init__(self):
            self.ajax_response = {'rc': 0, 'response': 'ok'}

        def add(self):
            form = BookmarkForm(request.GET)
            if not form.is_valid():
                ajax_response = {'rc': 1, 'response': form.errors.as_text()}
                return http.JsonResponse(ajax_response)

            form.save()
            return http.JsonResponse(self.ajax_response)

        def remove(self):
            pks = request.POST.getlist('pk')
            bks = Bookmark.objects.filter(pk__in=pks, user=request.user)
            bks.delete()

            return http.JsonResponse(self.ajax_response)

        def render(self):
            if request.GET.get('category'):
                bks = Bookmark.objects.filter(user=request.user,
                                              category_id=request.GET['category'])
            else:
                bks = Bookmark.objects.filter(user=request.user)

            context_data = {
                'user_profile': {'user': request.user},
                'bookmarks': bks,
            }
            return render(request, 'profile/bookmarks.html', context_data)

        def render_form(self):
            query = request.GET.copy()
            query['a'] = 'add'
            form = BookmarkForm(initial=query)
            form.populate(user=request.user)
            return http.HttpResponse(form.as_p())

    action = BookmarkActions()
    request_data = request.GET or request.POST
    func = getattr(action, request_data.get('a', 'render'))
    return func()


@require_http_methods(['GET', 'POST'])
@login_required
@csrf_protect
def profile(request, username):
    """Edit the profiles of the user"""
    u = get_object_or_404(User, username=username)

    try:
        up = UserProfile.get_user_profile(u)
    except ObjectDoesNotExist:
        up = UserProfile.objects.create(user=u)
    form = UserProfileForm(instance=up)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=up)
        if form.is_valid():
            form.save()
            messages.add_message(request,
                                 messages.SUCCESS,
                                 _('Information successfully updated'))
    context_data = {
        'user_profile': up,
        'form': form,
    }
    return render(request, 'profile/info.html', context_data)


@require_GET
@login_required
def dashboard(request):
    """List the recent plan/run"""
    runs_query = {
        'people': request.user,
        'is_active': True,
        'status': 'running',
    }

    tps = TestPlan.objects.filter(Q(author=request.user) | Q(owner=request.user))
    tps = tps.order_by('-plan_id')
    tps = tps.select_related('product', 'type')
    tps = tps.annotate(num_runs=Count('run', distinct=True))
    tps_active = tps.filter(is_active=True)
    trs = TestRun.list(runs_query)
    latest_fifteen_testruns = trs.order_by('-run_id')[:15]
    test_plans_disable_count = tps.count() - tps_active.count()

    context_data = {
        'user_profile': {'user': request.user},
        'test_plans_count': tps.count(),
        'test_plans_disable_count': test_plans_disable_count,
        'test_runs_count': trs.count(),
        'last_15_test_plans': tps_active[:15],
        'last_15_test_runs': latest_fifteen_testruns,
    }
    return render(request, 'profile/dashboard.html', context_data)
