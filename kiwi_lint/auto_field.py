from pylint import interfaces, checkers
from pylint.checkers import utils


class AutoFieldChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker, )

    name = 'auto-field-checker'

    msgs = {
        'R4521': (
            'Avoid using AutoField',
            'avoid-auto-field',
            'Avoid using django.db.models.AutoField'
        )
    }

    @utils.check_messages('avoid-auto-field')
    def visit_attribute(self, node):
        if node.attrname == 'AutoField':
            self.add_message('avoid-auto-field', node=node)
