from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView


@method_decorator(
    login_required, name="dispatch"
)  # pylint: disable=missing-permission-required
class TestingBreakdownView(TemplateView):

    template_name = "telemetry/testing/breakdown.html"


@method_decorator(
    login_required, name="dispatch"
)  # pylint: disable=missing-permission-required
class TestingStatusMatrixView(TemplateView):

    template_name = "telemetry/testing/status-matrix.html"


@method_decorator(
    login_required, name="dispatch"
)  # pylint: disable=missing-permission-required
class TestingExecutionTrendsView(TemplateView):

    template_name = "telemetry/testing/execution-trends.html"


@method_decorator(
    login_required, name="dispatch"
)  # pylint: disable=missing-permission-required
class TestingTestCaseHealth(TemplateView):

    template_name = "telemetry/testing/test-case-health.html"
