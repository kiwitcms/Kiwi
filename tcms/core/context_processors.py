# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils import timezone


def request_contents_processor(request):
    """
    Exposes only values that we need, not everything!
    """
    data = request.GET or request.POST
    return {
        "REQUEST__ALLOW_SELECT": data.get("allow_select"),
        "REQUEST__NEXT": data.get("next", ""),
        "REQUEST__NONAV": data.get("nonav"),
    }


def settings_processor(_request):
    """
    Django settings RequestContext Handler
    """
    return {"SETTINGS": settings}


def server_time_processor(_request):
    return {"SERVER_TIME": timezone.now()}
