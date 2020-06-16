from pylint import checkers
from pylint import interfaces


class FormFieldChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker, )

    name = 'form-field-label-checker'

    msgs = {
        'R4811': ('Do not use label in form Field class constructor.',
                  'form-field-label-used',
                  'Do not use label in form Field class constructor,'
                  'place template label in HTML. See:'
                  'https://github.com/kiwitcms/Kiwi/issues/738'),
        'R4812': ('Do not use help_text in form Field class constructor.',
                  'form-field-help-text-used',
                  'Do not use help_text in form Field class constructor,'
                  'place template help_text in HTML. See:'
                  'https://github.com/kiwitcms/Kiwi/issues/738'),
    }

    def visit_call(self, node):
        if node.func.as_string().endswith('Field') and node.keywords:
            for keyword in node.keywords:
                if keyword.arg == 'label':
                    self.add_message('form-field-label-used', node=node)
                if keyword.arg == 'help_text':
                    self.add_message('form-field-help-text-used', node=node)
