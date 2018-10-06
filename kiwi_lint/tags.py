# Copyright (c) 2018 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

import astroid

from pylint import interfaces
from pylint import checkers
from pylint.checkers import utils


class TagsChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker,)

    name = 'tags-checker'

    msgs = {'E4471': ("Don't use 'Tag.objects.get_or_create()', use 'Tag.get_or_create()'",
                      'tag-objects-get_or_create',
                      "Don't use 'Tag.objects.get_or_create()' because it doesn't respect "
                      "user permissions. Use class-method 'Tag.get_or_create()' instead!")}

    @utils.check_messages('tag-objects-get_or_create')
    def visit_attribute(self, node):
        if (node.attrname == 'get_or_create'
                and isinstance(node.expr, astroid.Attribute) and node.expr.attrname == 'objects'
                and isinstance(node.expr.expr, astroid.Name) and node.expr.expr.name == 'Tag'):
            self.add_message('tag-objects-get_or_create', node=node)
