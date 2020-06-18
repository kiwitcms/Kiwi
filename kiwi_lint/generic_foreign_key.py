import astroid
from pylint.checkers import utils, BaseChecker
from pylint.interfaces import IAstroidChecker
from pylint_django.utils import node_is_subclass


class GenericForeignKeyChecker(BaseChecker):
    __implements__ = (IAstroidChecker,)

    name = 'generic-foreign-key-checker'

    msgs = {
        'R5525': (
            'Avoid using GenericForeignKey',
            'avoid-generic-foreign-key',
            'Usage of django.contrib.contenttypes.fields.GenericForeignKey found'
            'Please make sure you delete all related records'
            'when this entity is deleted (e.g. using signal handlers)',
        )
    }

    @utils.check_messages('avoid-generic-foreign-key')
    def visit_classdef(self, node):

        if not node_is_subclass(node, 'django.db.models.base.Model'):
            return

        for part in node.body:
            if not isinstance(part, astroid.Assign):
                continue

            if 'GenericForeignKey' in part.value.func.as_string():
                self.add_message('avoid-generic-foreign-key', node=part.value)
