from pylint import interfaces, checkers
from pylint.checkers import utils


class DbColumnChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker, )

    name = 'db-column-checker'

    msgs = {
        'E4481': (
            'Avoid using db_column in Model fields',
            'avoid-db-column'
        )
    }

    @utils.check_messages('avoid-db-column')
    def visit_attribute(self, node):
        if (node.attrname == 'CharField'
                and isinstance(node.expr, astroid.Attribute) and node.expr.attrname == 'models'):
            self.add_message('avoid-db-column', node=node)
