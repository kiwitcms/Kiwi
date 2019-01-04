# Copyright (c) 2018 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from pylint import interfaces
from pylint import checkers
from pylint.checkers import utils


class AuthUserChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker,)

    name = 'auth-user-checker'

    msgs = {'E4441': ("Hard-coded 'auth.User'",
                      'hard-coded-auth-user',
                      "Don't hard-code the auth.User model. "
                      "Use settings.AUTH_USER_MODEL instead!"),
            'E4442': ("User model imported from django.contrib.auth.models",
                      'imported-auth-user',
                      "Don't import django.contrib.auth.models.User model. "
                      "Use django.contrib.auth.get_user_model() instead!")}

    @utils.check_messages('hard-coded-auth-user')
    def visit_const(self, node):
        # for now we don't check if the parent is a ForeignKey field
        # because the user model should not be hard-coded anywhere
        if node.value == 'auth.User':
            self.add_message('hard-coded-auth-user', node=node)

    def visit_importfrom(self, node):
        if node.modname == 'django.contrib.auth.models':
            for imported_names in node.names:
                if imported_names[0] in ['*', 'User']:
                    self.add_message('imported-auth-user', node=node)
                    break
