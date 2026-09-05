# Copyright (c) 2026 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from tcms.issuetracker.base import IssueTrackerType


class Bogus(IssueTrackerType):  # pylint: disable=abstract-method
    def __init__(self, bug_system, request):
        super().__init__(bug_system, request)
        raise RuntimeError("Used during testing")
