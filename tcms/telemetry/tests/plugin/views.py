# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django.shortcuts import render


def example(request):
    """An example view of Telemetry plugin"""
    return render(request, 'a_fake_plugin/example.html')
