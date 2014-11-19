# -*- coding: utf-8 -*-
from django import template

register = template.Library()


@register.filter(name='cutbystring')
def cut_by_string(value, arg):
    arg = int(arg)
    if len(value) < arg:
        return value
    else:
        return value[:arg - 3] + "..."


@register.filter(name='ismine')
def is_mine(object, user):
    if hasattr(object, 'author') and object.author == user:
        return True
    if hasattr(object, 'manager') and object.manager == user:
        return True

    return False


@register.filter(name='smart_unicode')
def smart_unicode(object):
    from django.utils.encoding import smart_unicode

    if not object:
        return object
    return smart_unicode(object)


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


@register.inclusion_tag('mail/new_run.txt', takes_context=True)
def absolute_url(context):
    request = context['request']
    object = context['test_run']
    if not hasattr(object, 'get_absolute_url'):
        return None

    return object.get_absolute_url(request)
