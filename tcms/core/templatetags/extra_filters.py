# -*- coding: utf-8 -*-
from django import template
from django.contrib.messages import constants as messages

register = template.Library()


@register.filter(name='smart_int')
def smart_int(object):
    if not object:
        return object

    try:
        return int(object)
    except ValueError:
        return object


@register.filter(name='message_icon')
def message_icon(msg):
    """
        Returns the string class name of a message icon
        which feeds directly into Patternfly.
    """
    icons = {
        messages.ERROR: 'error-circle-o',
        messages.WARNING: 'warning-triangle-o',
        messages.SUCCESS: 'ok',
        messages.INFO: 'info',
    }
    return 'pficon-' + icons[msg.level]
