# Copyright (c) 2018 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

import astroid

from pylint import interfaces
from pylint import checkers
from pylint.checkers import utils


class RawSQLChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker,)

    name = 'raw-sql-checker'

    msgs = {'E4431': ('Avoid using raw SQL',
                      'avoid-raw-sql',
                      'Avoid raw SQL, use Django ORM queries instead')}

    @utils.check_messages('avoid-raw-sql')
    def visit_attribute(self, node):
        # looking for .extra(select={}) patterns
        if node.attrname == 'extra' and isinstance(node.parent, astroid.Call):
            for keyword in node.parent.keywords:
                if keyword.arg in ['select', 'where', 'params',
                                   'tables', 'order_by', 'select_params']:
                    self.add_message('avoid-raw-sql', node=node)
                    break
