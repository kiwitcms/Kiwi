from pylint import checkers
from pylint.checkers import utils


class AutoFieldChecker(checkers.BaseChecker):
    name = "auto-field-checker"

    msgs = {
        "R4521": (
            "Avoid using AutoField",
            "avoid-auto-field",
            "Avoid using django.db.models.AutoField",
        )
    }

    @utils.only_required_for_messages("avoid-auto-field")
    def visit_attribute(self, node):
        if node.attrname == "AutoField":
            self.add_message("avoid-auto-field", node=node)
