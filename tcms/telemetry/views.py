# pylint: disable=missing-permission-required

from django.views.generic import TemplateView


class TestingBreakdownView(TemplateView):

    template_name = 'telemetry/testing/breakdown.html'


class TestingStatusMatrixView(TemplateView):

    template_name = 'telemetry/testing/status-matrix.html'


class TestingExecutionTrendsView(TemplateView):

    template_name = 'telemetry/testing/execution-trends.html'


class TestingTestCaseHealth(TemplateView):

    template_name = 'telemetry/testing/test-case-health.html'
