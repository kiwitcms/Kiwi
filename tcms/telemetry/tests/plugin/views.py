from django.shortcuts import render


def example(request):
    """An example view of Telemetry plugin"""
    return render(request, 'a_fake_plugin/example.html')
