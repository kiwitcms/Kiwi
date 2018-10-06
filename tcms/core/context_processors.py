# -*- coding: utf-8 -*-
from django.conf import settings


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
