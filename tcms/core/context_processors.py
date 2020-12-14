# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils import timezone


def request_contents_processor(request):
    """
    Django request contents RequestContext Handler
    """
    return {"REQUEST_CONTENTS": request.GET or request.POST}


def settings_processor(_request):
    """
    Django settings RequestContext Handler
    """
    return {"SETTINGS": settings}


def server_time_processor(_request):
    return {"SERVER_TIME": timezone.now()}
