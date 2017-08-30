# -*- coding: utf-8 -*-
from django import template

register = template.Library()


@register.filter(name='smart_int')
def smart_int(object):
    if not object:
        return object

    try:
        return int(object)
    except ValueError:
        return object


@register.filter(name='timedelta2string')
def timedelta2string(object):
    from tcms.core.utils.timedeltaformat import format_timedelta

    return format_timedelta(object)


@register.filter(name='timedelta2seconds')
def timedelta2seconds(object):
    return int(object.seconds + object.days * 86400)
