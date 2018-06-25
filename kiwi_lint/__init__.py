# Copyright (c) 2018 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

# NOTE: import order matches the numeric ID of the checker
from .dunder_attributes import DunderClassAttributeChecker
from .list_comprehension import ListComprehensionChecker
from .docstring import DocstringChecker
from .raw_sql import RawSQLChecker


def register(linter):
    linter.register_checker(DunderClassAttributeChecker(linter))
    linter.register_checker(ListComprehensionChecker(linter))
    linter.register_checker(DocstringChecker(linter))
    linter.register_checker(RawSQLChecker(linter))
