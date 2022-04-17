from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView


@method_decorator(login_required, name="dispatch")
class TestingBreakdownView(TemplateView):  # pylint: disable=missing-permission-required
    template_name = "telemetry/testing/breakdown.html"


@method_decorator(login_required, name="dispatch")
class TestingStatusMatrixView(
    TemplateView
):  # pylint: disable=missing-permission-required
    template_name = "telemetry/testing/status-matrix.html"


@method_decorator(login_required, name="dispatch")
class TestingExecutionTrendsView(
    TemplateView
):  # pylint: disable=missing-permission-required
    template_name = "telemetry/testing/execution-trends.html"


@method_decorator(login_required, name="dispatch")
class TestingTestCaseHealth(
    TemplateView
):  # pylint: disable=missing-permission-required
    template_name = "telemetry/testing/test-case-health.html"
