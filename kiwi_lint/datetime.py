"""
    Warns against usage of datetime.now() which may not be fully timezone
    safe. Instead we should use django.utils.timezone.now() which acts
    according to settings!
"""

from astroid import nodes

from pylint import checkers
from pylint import interfaces


class DatetimeChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker, )

    name = 'datetime-checker'

    msgs = {
        'R4711': ('Do not use datetime.now(), use django.utils.timezone.now()',
                  'datetime-now-used',
                  'Use django.utils.timezone.now()! See: '
                  'https://docs.djangoproject.com/en/2.2/topics/i18n/timezones/'
                  '#interpretation-of-naive-datetime-objects')
    }

    def visit_name(self, node):
        parent = node.parent
        while node.name == 'datetime' and isinstance(parent, nodes.Attribute):
            if parent.attrname == 'now':
                self.add_message('datetime-now-used', node=node)
            parent = parent.parent
