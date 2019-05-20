from django.views.generic import TemplateView


class TestingBreakdownView(TemplateView):

    template_name = 'telemetry/testing/breakdown.html'


class TestingStatusMatrixView(TemplateView):

    template_name = 'telemetry/testing/status-matrix.html'
