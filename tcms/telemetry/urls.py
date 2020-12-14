from django.urls import re_path

from tcms.telemetry import views

urlpatterns = [
    re_path(
        r"^testing/breakdown/$",
        views.TestingBreakdownView.as_view(),
        name="testing-breakdown",
    ),
    re_path(
        r"^testing/status-matrix/$",
        views.TestingStatusMatrixView.as_view(),
        name="testing-status-matrix",
    ),
    re_path(
        r"^testing/execution-trends/$",
        views.TestingExecutionTrendsView.as_view(),
        name="testing-execution-trends",
    ),
    re_path(
        r"^testing/test-case-health/$",
        views.TestingTestCaseHealth.as_view(),
        name="test-case-health",
    ),
]
