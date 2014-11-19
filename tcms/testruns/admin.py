# -*- coding: utf-8 -*-
from django.contrib import admin

from tcms.testruns.models import TestCaseRunStatus
from tcms.testruns.models import TestRun


class TestRunAdmin(admin.ModelAdmin):
    # search_fields=(('run_id',))
    list_filter = ['manager', 'default_tester']
    list_display = ('run_id', 'estimated_time', 'plan')


class TestCaseRunStatusAdmin(admin.ModelAdmin):
    search_fields = (('name',))
    list_display = ('id', 'name', 'description', 'sortkey')


admin.site.register(TestRun, TestRunAdmin)
admin.site.register(TestCaseRunStatus, TestCaseRunStatusAdmin)
