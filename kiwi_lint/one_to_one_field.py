from pylint import checkers
from pylint.checkers import utils


class OneToOneFieldChecker(checkers.BaseChecker):
    name = "one-to-one-field-checker"

    msgs = {
        "R4531": (
            "Do not use OneToOneField",
            "one-to-one-field",
            "Do not use OneToOneField because it does not play well with the"
            "history framework (this relation does not have enabled history",
        )
    }

    @utils.only_required_for_messages("one-to-one-field")
    def visit_attribute(self, node):
        if node.attrname == "OneToOneField":
            self.add_message("one-to-one-field", node=node)
