# Copyright (c) 2018 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

import os

import astroid

from pylint import interfaces
from pylint import checkers
from pylint.checkers import utils


class EmptyModuleChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker,)

    name = 'empty-module-checker'

    msgs = {'E4481': ("Remove empty module from git!",
                      'remove-empty-module',
                      "Kiwi TCMS doesn't need to carry around modules which are empty. "
                      "They must be removed from the source code!")}

    @utils.check_messages('remove-empty-module')
    def visit_module(self, node):
        if not node.body and not node.path[0].endswith('__init__.py'):
            self.add_message('remove-empty-module', node=node)


class ModuleInDirectoryWithoutInitChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker,)

    name = 'dir-without-init-checker'

    msgs = {'R4482': ("File '%s' is in directory without __init__.py",
                      'module-in-directory-without-init',
                      "Python module is found inside a directory which is "
                      "missing __init__.py! This will lead to missing packages when "
                      "tarball is built for distribution on PyPI! See "
                      "https://github.com/kiwitcms/Kiwi/issues/790")}

    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'tcms'))

    # NOTE: this works against tcms/ directory and will not take into account
    # if we want to examine only a sub-dir or a few files
    # all files found by os.walk
    all_python_files = set()
    # all modules found by pylint, which conveniently skips files/dirs
    # with missing __init__.py
    discovered_python_files = set()

    def open(self):
        for root, _dirs, files in os.walk(self.project_root, topdown=False):
            # skip migrations
            if root.find('migrations') > -1:
                continue

            for file_name in files:
                if file_name.endswith('.py'):
                    self.all_python_files.add(
                        os.path.join(self.project_root, root, file_name))

    def visit_module(self, node):
        for file_name in node.path:
            self.discovered_python_files.add(file_name)

    @utils.check_messages('module-in-directory-without-init')
    def close(self):
        diff = self.all_python_files - self.discovered_python_files
        diff = list(diff)
        diff.sort()

        dir_prefix = os.path.dirname(self.project_root) + '/'
        for fname in diff:
            fname = fname.replace(dir_prefix, '')
            self.add_message('module-in-directory-without-init', args=(fname,))


class EmptyClassChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker,)

    name = 'empty-class-checker'

    msgs = {'E4483': ("Remove empty class from git!",
                      'remove-empty-class',
                      "Kiwi TCMS doesn't need to carry around classes which are empty. "
                      "They must be removed from the source code!")}

    @utils.check_messages('remove-empty-class')
    def visit_classdef(self, node):
        if not node.body:
            self.add_message('remove-empty-class', node=node)

        for child in node.body:
            if isinstance(child, astroid.Pass):
                self.add_message('remove-empty-class', node=node)
