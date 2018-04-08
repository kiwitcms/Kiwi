# Copyright (c) 2018 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

import astroid

from pylint import interfaces
from pylint import checkers
from pylint.checkers import utils


class DunderClassAttributeChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker,)

    name = 'dunder-class-attribute-checker'

    msgs = {'C4401': ('Class attributes should not contain double underscores',
                      'dunder-class-attribute',
                      'Dunders, e.g. "__some_name__", are reserved for Python. '
                      'Do not name your class attributes this way!')}

    @utils.check_messages('dunder-class-attribute')
    def visit_classdef(self, node):
        """Detect when class attributes use double underscores."""
        # we can redefine special methods (e.g. __iter__) and some attributes,
        # e.g. __doc__, by declaring them as class attributes. Exclude them from the
        # test below.
        allowed_attributes = dir([])

        for child in node.body:
            if isinstance(child, astroid.Assign):
                for target in child.targets:
                    if (isinstance(target, astroid.AssignName)
                            and target.name not in allowed_attributes
                            and target.name.startswith('__')
                            and target.name.endswith('__')):
                        self.add_message('dunder-class-attribute', node=child)
