# Copyright (c) 2021,2023 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from pylint import checkers

from .utils import is_api_function


class APIDistinctChecker(checkers.BaseChecker):
    """
    Will inspect API functions for the presence of .distinct() query!
    """

    current_api_method = None
    distinct_found = False

    name = "api-distinct-checker"

    msgs = {
        "R4910": (
            "API function is missing .distinct() in queryset!",
            "api-distinct-required",
            "All API functions must return distinct results!",
        )
    }

    def visit_functiondef(self, node):
        self.current_api_method = None
        self.distinct_found = False

        # for now only check filter() functions
        if node.name != "filter":
            return

        if not is_api_function(node):
            return

        self.current_api_method = node

    def visit_attribute(self, node):
        if node.attrname == "distinct" and node.frame() is self.current_api_method:
            self.distinct_found = True

    def leave_functiondef(self, node):
        # no API method in scope
        if not self.current_api_method:
            return

        if not self.distinct_found:
            self.add_message("api-distinct-required", node=node)
