from pylint import checkers
from pylint.checkers import utils


class DbColumnChecker(checkers.BaseChecker):
    name = "db-column-used"

    msgs = {
        "E4841": (
            "Do not use db_column in model field definitions",
            "db-column-used",
            "Do not use db_column argument in model field definitions,"
            "See: https://github.com/kiwitcms/Kiwi/issues/736",
        )
    }

    @utils.only_required_for_messages("db-column-used")
    def visit_keyword(self, node):
        if node.arg == "db_column":
            self.add_message("db-column-used", node=node)
