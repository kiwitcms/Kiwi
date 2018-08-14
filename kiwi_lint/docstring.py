# Copyright (c) 2018 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

import tokenize

from pylint import interfaces
from pylint import checkers
from pylint.checkers import utils


class DocstringChecker(checkers.BaseTokenChecker):
    __implements__ = (interfaces.ITokenChecker, interfaces.IAstroidChecker,)

    name = 'docstring-checker'

    msgs = {'R4421': ('Use """ for docstrings',
                      'use-triple-double-quotes',
                      'Use """ for docstrings!')}

    _string_tokens = {}

    def process_tokens(self, tokens):
        """
            Note: this method is executed before all of the visit_ methods
            and self._string_tokens will contain all possible strings
            before we try linting docstrings!
        """
        for (tok_type, token, (_start_row, _start_col), (_end_row, _end_col), _line) in tokens:
            if tok_type == tokenize.STRING:
                # 'token' is the whole un-parsed token; we can look at the start
                # of it to see whether it's a raw or unicode string etc.
                # 'text_token' is the text without the quites
                text_token = token.replace('"', '').replace("'", "")
                # NOTE: this is sub-optimal b/c same tokens will override
                # any previous ones which may not be complacent to the
                # triple double quotes policy. However this isn't a big deal
                # because it's unlikely to have exactly the same docstrings
                # and it is more likely for them to diverge over time and
                # expose the problem with quotes!
                self._string_tokens[text_token] = token

    def visit_module(self, node):
        self._check_docstring(node)

    def visit_classdef(self, node):
        self._check_docstring(node)

    def visit_functiondef(self, node):
        self._check_docstring(node)

    @utils.check_messages('use-triple-double-quotes')
    def _check_docstring(self, node):
        if node.doc in self._string_tokens:
            token = self._string_tokens[node.doc]
            if not token.startswith('"""'):
                self.add_message('use-triple-double-quotes', node=node)
