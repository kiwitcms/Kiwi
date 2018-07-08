# Copyright (c) 2018 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

# NOTE: import order matches the numeric ID of the checker
from .dunder_attributes import DunderClassAttributeChecker
from .list_comprehension import ListComprehensionChecker
from .docstring import DocstringChecker
from .raw_sql import RawSQLChecker
from .auth_user import AuthUserChecker
from .bulk_create import BulkCreateChecker
from .objects_update import ObjectsUpdateChecker


def register(linter):
    linter.register_checker(DunderClassAttributeChecker(linter))
    linter.register_checker(ListComprehensionChecker(linter))
    linter.register_checker(DocstringChecker(linter))
    linter.register_checker(RawSQLChecker(linter))
    linter.register_checker(AuthUserChecker(linter))
    linter.register_checker(BulkCreateChecker(linter))
    linter.register_checker(ObjectsUpdateChecker(linter))
