# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

import astroid

from pylint import interfaces
from pylint import checkers


class MissingPermissionsChecker(checkers.BaseChecker):
    """
        Will inspect functions and classes inside a views.py module for the
        presence of permissions decorator. May generate lots of false negatives
        but we're ok with that. Better inspect than forget to add permission
        decorator!
    """
    allowed_decorators = [
        'permission_required',
        'object_permission_required',
    ]
    inside_views_module = False

    __implements__ = (interfaces.IAstroidChecker,)

    name = 'mising-permissions-checker'

    msgs = {'R4511': ("View is missing @permission_required decorator!",
                      'missing-permission-required',
                      "All views must require permissions!")}

    def visit_module(self, node):
        self.inside_views_module = node.name.endswith('.views')

    def visit_functiondef(self, node):
        if not self.inside_views_module:
            return

        arg0 = None
        if node.args.args:
            arg0 = node.args.args[0]

        if arg0 and arg0.name != 'request':
            return
        # this function is a confirmed view so start checking
        self._check_for_missing_decorator(node)

    def visit_classdef(self, node):
        if not self.inside_views_module:
            return

        # class based views always inherit from something
        # tip: we can be more precise what base classes are allowed in order
        # to identify cbv more correctly! Leaving it like that for now and will
        # revisit later if we start to see many false negatives!
        if not node.bases:
            return

        # for now we check all classes in views.py modules
        # until we learn how to recognize class based views
        self._check_for_missing_decorator(node)

    def _check_for_missing_decorator(self, node):
        if not isinstance(node.parent, astroid.scoped_nodes.Module):
            return

        if not node.decorators:
            self.add_message('missing-permission-required', node=node)
            return

        found_permissions_required = False
        for decorator in node.decorators.nodes:
            if isinstance(decorator, astroid.Call):
                if decorator.func.name in self.allowed_decorators:
                    found_permissions_required = True
                    break
                if decorator.func.name == 'method_decorator' and \
                        isinstance(decorator.args[0], astroid.Call) and \
                        decorator.args[0].func.name in self.allowed_decorators:
                    found_permissions_required = True
                    break

        if not found_permissions_required:
            self.add_message('missing-permission-required', node=node)


class MissingAPIPermissionsChecker(checkers.BaseChecker):
    """
        Will inspect API functions for the presence of permissions decorator!
    """
    __implements__ = (interfaces.IAstroidChecker,)

    name = 'mising-api-permissions-checker'

    msgs = {'R4512': ("API function is missing @permissions_required decorator!",
                      'missing-api-permissions-required',
                      "All API functions must require permissions!")}

    def visit_functiondef(self, node):
        # API functions always have @rpc_method decorator
        if not node.decorators:
            return

        is_api_function = False
        for decorator in node.decorators.nodes:
            if isinstance(decorator, astroid.Call) and \
                    isinstance(decorator.func, astroid.Name) and \
                    decorator.func.name == 'rpc_method':
                is_api_function = True
                break

        if not is_api_function:
            return

        found_permissions_required = False
        for decorator in node.decorators.nodes:
            if isinstance(decorator, astroid.Call) and \
                    isinstance(decorator.func, astroid.Name) and \
                    decorator.func.name == 'permissions_required':
                found_permissions_required = True
                break

            if isinstance(decorator, astroid.Name) and \
                    decorator.name == 'http_basic_auth_login_required':
                found_permissions_required = True
                break

        if not found_permissions_required:
            self.add_message('missing-api-permissions-required', node=node)
