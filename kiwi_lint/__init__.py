# Copyright (c) 2018 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from .dunder_attributes import DunderClassAttributeChecker


def register(linter):
    linter.register_checker(DunderClassAttributeChecker(linter))
