# Copyright (c) 2018 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from pylint import interfaces
from pylint import checkers
from pylint.checkers import utils


class EmptyModuleChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker,)

    name = 'empty-module-checker'

    msgs = {'E4481': ("Remove empty module from git!",
                      'remove-empty-module',
                      "Kiwi TCMS doesn't need to carry around modules which are empty. "
                      "They must be removed from the source code!")}

    @utils.check_messages('remove-empty-module')
    def visit_module(self, node):
        if not node.body and not node.path[0].endswith('__init__.py'):
            self.add_message('remove-empty-module', node=node)
