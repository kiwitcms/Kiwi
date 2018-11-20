"""
    Custom template tag filters.
"""

import markdown

from django import template
from django.utils.safestring import mark_safe
from django.contrib.messages import constants as messages

register = template.Library()


@register.filter(name='markdown2html')
def markdown2html(md_str):
    """
        Returns markdown string as HTML.
    """
    return mark_safe(markdown.markdown(md_str,  # nosec:B308:blacklist
                                       extensions=['markdown.extensions.fenced_code',
                                                   'markdown.extensions.nl2br']))


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
