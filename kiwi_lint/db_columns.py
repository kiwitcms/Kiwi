from pylint import interfaces, checkers
from pylint.checkers import utils


class AutoFieldChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker, )

    name = 'db-columns-checker'

    msgs = {
        'E4480': (
            'Avoid using db_columns in Model fields',
            'avoid-db-columns'
        )
    }

    @utils.check_messages('avoid-db-column')
    def visit_attribute(self, node):
        if node.attrname == 'db_column':
            self.add_message('avoid-db-columns', node=node)
