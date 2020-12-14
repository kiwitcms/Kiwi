"""
    Custom template tag filters.
"""

import bleach
import markdown
from bleach_allowlist import markdown_attrs, markdown_tags, print_attrs, print_tags
from django import template
from django.contrib.messages import constants as messages
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="is_list")
def is_list(variable):
    return isinstance(variable, list)


@register.filter(name="markdown2html")
def markdown2html(md_str):
    """
    Returns markdown string as HTML.
    """
    if md_str is None:
        md_str = ""

    rendered_md = markdown.markdown(
        md_str,
        extensions=[
            "markdown.extensions.codehilite",
            "markdown.extensions.fenced_code",
            "markdown.extensions.nl2br",
            "markdown.extensions.tables",
            "tcms.utils.markdown",
        ],
    )

    html = bleach.clean(
        rendered_md,
        markdown_tags + print_tags + ["del", "s"],
        {**markdown_attrs, **print_attrs},
    )
    return mark_safe(html)  # nosec:B308:blacklist


@register.filter(name="message_icon")
def message_icon(msg):
    """
    Returns the string class name of a message icon
    which feeds directly into Patternfly.
    """
    icons = {
        messages.ERROR: "error-circle-o",
        messages.WARNING: "warning-triangle-o",
        messages.SUCCESS: "ok",
        messages.INFO: "info",
    }
    return "pficon-" + icons[msg.level]
