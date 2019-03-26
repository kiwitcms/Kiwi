# -*- coding: utf-8 -*-

from django.contrib import admin

from tcms.project.models import Project


class ProjectAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'enabled')
    list_filter = ('enabled',)


admin.site.register(Project, ProjectAdmin)
