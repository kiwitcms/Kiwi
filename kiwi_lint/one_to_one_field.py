from pylint import interfaces
from pylint import checkers
from pylint.checkers import utils


class OneToOneFieldChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker,)

    name = 'one-to-one-field-checker'

    msgs = {'R4531': ("Do not use OneToOneField",
                      'one-to-one-field',
                      "Do not use OneToOneField because it does not play well with the"
                      "history framework (this relation does not have enabled history")}

    @utils.check_messages('one-to-one-field')
    def visit_attribute(self, node):
        if node.attrname == 'OneToOneField':
            self.add_message('one-to-one-field', node=node)
