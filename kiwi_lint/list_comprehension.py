# Copyright (c) 2018 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from pylint import interfaces
from pylint import checkers
from pylint.checkers import utils


class ListComprehensionChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker,)

    name = 'list-comprehension-checker'

    msgs = {'R4411': ('Avoid using list comprehensions',
                      'avoid-list-comprehension',
                      'List comprehensions are harder to read and debug '
                      'so try to avoid them!')}

    @utils.check_messages('avoid-list-comprehension')
    def visit_listcomp(self, node):
        self.add_message('avoid-list-comprehension', node=node)
