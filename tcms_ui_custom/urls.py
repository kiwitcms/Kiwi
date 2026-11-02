from django.urls import path
from .views import projects, testcases, settings, testplans, testruns, dashboard

urlpatterns = [
    # --- DASHBOARD ---
    path('', dashboard.dashboard, name='dashboard'),

    # --- PROJECTS ---
    path('settings/projects/', projects.project_settings, name='project_settings'),
    path('settings/projects/new/', projects.project_create, name='project_create'),
    path('settings/projects/<int:pk>/edit/', projects.project_edit, name='project_edit'),
    path('projects/<int:pk>/', projects.project_overview, name='project_overview'),

    # --- MODULES (COMPONENTS) ---
    path('components/<int:pk>/edit/', projects.component_edit, name='component_edit'),
    path('components/<int:pk>/delete/', projects.component_delete, name='component_delete'),

    # --- VERSIONS & BUILDS ---
    path('projects/<int:pk>/versions/new/', projects.version_create, name='version_create'),
    path('projects/<int:pk>/versions/<int:version_pk>/delete/', projects.version_delete, name='version_delete'),
    path('projects/<int:pk>/builds/new/', projects.build_create, name='build_create'),
    path('projects/<int:pk>/builds/<int:build_pk>/delete/', projects.build_delete, name='build_delete'),

    # --- TEST CASES ---
    path('repository/', testcases.testcase_list, name='testcase_list'),
    path('repository/new/', testcases.testcase_create, name='testcase_create'),
    path('repository/<int:pk>/', testcases.testcase_view, name='testcase_view'),
    path('repository/<int:pk>/edit/', testcases.testcase_edit, name='testcase_edit'),
    path('repository/<int:pk>/delete/', testcases.testcase_delete, name='testcase_delete'),

    # --- TEST PLANS ---
    path('plans/', testplans.testplan_list, name='testplan_list'),
    path('plans/new/', testplans.testplan_create, name='testplan_create'),
    path('plans/<int:pk>/', testplans.testplan_detail, name='testplan_detail'),
    path('plans/<int:pk>/toggle/', testplans.testplan_toggle_active, name='testplan_toggle_active'),

    # --- TEST RUNS ---
    path('executions/<int:pk>/', testruns.testrun_detail, name='testrun_detail'),
    path('executions/<int:pk>/edit/', testruns.testrun_edit, name='testrun_edit'),
    path('executions/<int:run_pk>/execute/<int:case_pk>/', testruns.execute_test, name='execute_test'),

    # --- APIS ---
    path('api/get-testcases/', testplans.api_get_testcases, name='api_get_testcases'),
    path('api/get-modules/', testplans.api_get_modules, name='api_get_modules'),
    path('api/get-versions/', testplans.api_get_versions, name='api_get_versions'),

    # --- SETTINGS HUB ---
    path('settings/', settings.settings_index, name='settings_index'),
    path('settings/priorities/', settings.settings_priorities, name='settings_priorities'),
    path('settings/priorities/<int:pk>/edit/', settings.priority_edit, name='priority_edit'),
    path('settings/priorities/<int:pk>/delete/', settings.priority_delete, name='priority_delete'),
    path('settings/statuses/', settings.settings_statuses, name='settings_statuses'),
    path('settings/statuses/<int:pk>/edit/', settings.status_edit, name='status_edit'),
    path('settings/statuses/<int:pk>/delete/', settings.status_delete, name='status_delete'),
    path('settings/tags/', settings.settings_tags, name='settings_tags'),
    path('settings/tags/<int:pk>/edit/', settings.tag_edit, name='tag_edit'),
    path('settings/tags/<int:pk>/delete/', settings.tag_delete, name='tag_delete'),
]
