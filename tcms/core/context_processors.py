# -*- coding: utf-8 -*-
from django.conf import settings


def admin_prefix_processor(request):
    """
    Django Admin URL Prefix RequestContext Handler
    """
    return {'ADMIN_PREFIX': settings.ADMIN_PREFIX}


def auth_backend_processor(request):
    """Determine the be able to login/logout/register request """
    from tcms.core.contrib.auth import get_using_backend

    return {'AUTH_BACKEND': get_using_backend()}


def request_contents_processor(request):
    """
    Django request contents RequestContext Handler
    """
    return {'REQUEST_CONTENTS': request.REQUEST}


def settings_processor(request):
    """
    Django settings RequestContext Handler
    """
    return {'SETTINGS': settings}
