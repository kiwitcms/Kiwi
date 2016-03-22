# -*- coding: utf-8 -*-
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponse, Http404
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from tcms.core.utils.raw_sql import RawSQL
from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestRun
from tcms.profiles.models import Bookmark
from tcms.profiles.forms import BookmarkForm, UserProfileForm


MODULE_NAME = 'profile'


# @user_passes_test(lambda u: u.username == username)
@login_required
def bookmark(request, username, template_name='profile/bookmarks.html'):
    """
    Bookmarks for the user
    """

    if username != request.user.username:
        return HttpResponseRedirect(reverse('django.contrib.auth.views.login'))
    else:
        up = {'user': request.user}

    class BookmarkActions(object):
        def __init__(self):
            self.ajax_response = {
                'rc': 0,
                'response': 'ok',
            }

        def add(self):
            form = BookmarkForm(request.REQUEST)
            if not form.is_valid():
                ajax_response = {
                    'rc': 1,
                    'response': form.errors.as_text(),
                }
                return HttpResponse(json.dumps(ajax_response))

            form.save()
            return HttpResponse(json.dumps(self.ajax_response))

        def add_category(self):
            pass

        def remove(self):
            pks = request.REQUEST.getlist('pk')
            bks = Bookmark.objects.filter(
                pk__in=pks,
                user=request.user,
            )
            bks.delete()

            return HttpResponse(json.dumps(self.ajax_response))

        def render(self):
            if request.REQUEST.get('category'):
                bks = Bookmark.objects.filter(
                    user=request.user,
                    category_id=request.REQUEST['category']
                )
            else:
                bks = Bookmark.objects.filter(user=request.user)

            context_data = {
                'user_profile': up,
                'bookmarks': bks,
            }
            return render_to_response(template_name, context_data,
                                      context_instance=RequestContext(request))

        def render_form(self):
            query = request.GET.copy()
            query['a'] = 'add'
            form = BookmarkForm(initial=query)
            form.populate(user=request.user)
            return HttpResponse(form.as_p())

    action = BookmarkActions()
    func = getattr(action, request.REQUEST.get('a', 'render'))
    return func()


@login_required
@csrf_protect
def profile(request, username, template_name='profile/info.html'):
    """
    Edit the profiles of the user
    """

    try:
        u = User.objects.get(username=username)
    except ObjectDoesNotExist, error:
        raise Http404(error)

    try:
        up = u.get_profile()
    except ObjectDoesNotExist:
        up = u.profile.create()
    message = None
    form = UserProfileForm(instance=up)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=up)
        if form.is_valid():
            form.save()
            message = 'Information successfully updated.'
    context_data = {
        'user_profile': up,
        'form': form,
        'message': message,
    }
    return render_to_response(template_name, context_data,
                              context_instance=RequestContext(request))


@login_required
def recent(request, username, template_name='profile/recent.html'):
    """
    List the recent plan/run.
    """

    if username != request.user.username:
        return HttpResponseRedirect(reverse('django.contrib.auth.views.login'))
    else:
        up = {'user': request.user}

    runs_query = {
        'people': request.user,
        'is_active': True,
        'status': 'running',
    }

    tps = TestPlan.objects.filter(
        Q(author=request.user) | Q(owner=request.user))
    tps = tps.order_by('-plan_id')
    tps = tps.select_related('product', 'type')
    tps = tps.extra(select={
        'num_runs': RawSQL.num_runs,
    })
    tps_active = tps.filter(is_active=True)
    trs = TestRun.list(runs_query)
    latest_fifteen_testruns = trs.order_by('-run_id')[:15]
    test_plans_disable_count = tps.count() - tps_active.count()

    context_data = {
        'module': MODULE_NAME,
        'user_profile': up,
        'test_plans_count': tps.count(),
        'test_plans_disable_count': test_plans_disable_count,
        'test_runs_count': trs.count(),
        'last_15_test_plans': tps_active[:15],
        'last_15_test_runs': latest_fifteen_testruns,
    }
    return render_to_response(template_name, context_data,
                              context_instance=RequestContext(request))


@login_required
def redirect_to_profile(request):
    return HttpResponseRedirect(
        reverse('tcms.profiles.views.recent', args=[request.user.username]))
