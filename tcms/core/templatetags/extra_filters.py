# -*- coding: utf-8 -*-
from django import template
from django.contrib.messages import constants as messages

register = template.Library()


@register.filter(name='to_int')
def to_int(obj):
    """
        Returns int representation. Use in only 2 places where
        we compare query string parameter with a current value to
        determine if an <option> is selected!

        NOTE: We can get rid of this once REQUEST_CONTENTS is gone!
    """
    try:
        return int(obj)
    except ValueError:
        return obj


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
