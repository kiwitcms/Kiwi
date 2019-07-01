from django.views.generic import TemplateView


class TestingBreakdownView(TemplateView):  # pylint: disable=missing-permission-required

    template_name = 'telemetry/testing/breakdown.html'


class TestingStatusMatrixView(TemplateView):  # pylint: disable=missing-permission-required

    template_name = 'telemetry/testing/status-matrix.html'


class TestingExecutionTrendsView(TemplateView):

    template_name = 'telemetry/testing/execution-trends.html'
