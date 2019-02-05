# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

import astroid

from pylint import interfaces
from pylint import checkers
from pylint.checkers import utils


class NestedDefinitionChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker,)

    name = 'nested-definition-checker'

    msgs = {'E4491': ("Nested class definition found!",
                      'nested-class-found',
                      "Do not define classes inside other classes or functions!"),
            'E4492': ("Nested function definition found!",
                      'nested-function-found',
                      "Do not define functions inside other functions!")}

    @utils.check_messages('nested-function-found')
    def visit_functiondef(self, node):
        if not isinstance(node.parent, (astroid.Module, astroid.ClassDef)):
            self.add_message('nested-function-found', node=node)

    @utils.check_messages('nested-class-found')
    def visit_classdef(self, node):
        if not isinstance(node.parent, astroid.Module) and node.name not in ['Meta', 'Media']:
            self.add_message('nested-class-found', node=node)
