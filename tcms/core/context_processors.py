# -*- coding: utf-8 -*-
from django.conf import settings


def auth_backend_processor(_request):
    """Determine the be able to login/logout/register request """
    from tcms.core.contrib.auth import get_using_backend

    return {'AUTH_BACKEND': get_using_backend()}


def request_contents_processor(request):
    """
    Django request contents RequestContext Handler
    """
    return {'REQUEST_CONTENTS': request.GET or request.POST}


def settings_processor(_request):
    """
    Django settings RequestContext Handler
    """
    return {'SETTINGS': settings}
