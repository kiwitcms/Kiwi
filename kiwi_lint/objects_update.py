# Copyright (c) 2018 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from pylint import interfaces
from pylint import checkers
from pylint.checkers import utils


class ObjectsUpdateChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker,)

    name = 'objects-update-checker'

    msgs = {'E4461': ("Model.objects.update() doesn't update history! Use Model.save() instead.",
                      'objects-update-used',
                      "")}

    @utils.check_messages('objects-update-used')
    def visit_attribute(self, node):
        """
            Note: this checker will produce false-positives on
            dict.update() or anything else that is named .update().

            These should be white-listed on a line by line basis
            b/c there can be many situations where .update() is used
            after filtering or directly on top of another variable which
            itself is a query set.
        """
        if node.attrname == 'update':
            # white-list
            if node.as_string() == 'context.update':
                return
            if node.as_string() == 'data.update':
                return
            self.add_message('objects-update-used', node=node)
