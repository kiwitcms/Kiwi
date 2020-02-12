# pylint: disable=no-self-use
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from tcms.core.history import ReadOnlyHistoryAdmin
from tcms.testruns.models import TestRun, TestExecutionStatus


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


class TestExecutionStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'visual_icon', 'name', 'colored_color', 'weight')
    ordering = ['-weight']

    def colored_color(self, test_execution):
        return format_html(
            '''
            <span style="background-color: {}; height: 20px; display: block;
                         color: black; font-weight: bold">
                {}
            </span>
            ''',
            test_execution.color, test_execution.color)

    colored_color.short_description = 'color'

    def visual_icon(self, test_execution):
        return format_html(
            '''
            <span class="{}" style="font-size: 18px; color: {};"></span>
            ''',
            test_execution.icon, test_execution.color
        )

    visual_icon.short_description = 'icon'


admin.site.register(TestRun, TestRunAdmin)
admin.site.register(TestExecutionStatus, TestExecutionStatusAdmin)
