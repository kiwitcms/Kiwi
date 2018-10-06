# pylint: disable=no-self-use
from django.urls import reverse
from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from tcms.core.history import ReadOnlyHistoryAdmin
from tcms.testruns.models import TestRun


class TestRunAdmin(ReadOnlyHistoryAdmin):
    actions = ['delete_selected']

    def add_view(self, request, form_url='', extra_context=None):
        return HttpResponseRedirect(reverse('admin:testruns_testrun_changelist'))

    def change_view(self, request, object_id, form_url='', extra_context=None):
        return HttpResponseRedirect(reverse('testruns-get', args=[object_id]))

    @admin.options.csrf_protect_m
    def delete_view(self, request, object_id, extra_context=None):
        test_run = TestRun.objects.get(pk=object_id)
        if request.user.is_superuser or request.user in [test_run.manager, test_run.plan.author]:
            return super().delete_view(request, object_id, extra_context)

        messages.add_message(request,
                             messages.ERROR,
                             _('Permission denied: TestRun does not belong to you'))
        return HttpResponseRedirect(reverse('testruns-get', args=[object_id]))


admin.site.register(TestRun, TestRunAdmin)
