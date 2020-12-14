import astroid
from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker


class GenericForeignKeyChecker(BaseChecker):
    __implements__ = (IAstroidChecker,)

    name = "generic-foreign-key-checker"

    msgs = {
        "E4851": (
            "Avoid defining GenericForeignKey fields",
            "avoid-generic-foreign-key",
            "Avoid defining GenericForeignKey fields in models,"
            "See: https://github.com/kiwitcms/Kiwi/issues/1303",
        )
    }

    @utils.check_messages("avoid-generic-foreign-key")
    def visit_call(self, node):
        if (
            isinstance(node.func, astroid.Name)
            and node.func.name == "GenericForeignKey"
        ):
            self.add_message("avoid-generic-foreign-key", node=node)
        if (
            isinstance(node.func, astroid.Attribute)
            and node.func.attrname == "GenericForeignKey"
        ):
            self.add_message("avoid-generic-foreign-key", node=node)
