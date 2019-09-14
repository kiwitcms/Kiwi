# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from tcms.issuetracker.types import from_name
from tcms.testcases.models import BugSystem


def tracker_from_url(url):
    """
        Return the IssueTrackerType object for the system
        where ``base_url`` is part of ``url``. Usually we pass
        URLs to pre-existing defects to this method.
    """
    for bug_system in BugSystem.objects.all():
        if bug_system.base_url and url.startswith(bug_system.base_url):
            return from_name(bug_system.tracker_type)(bug_system)

    return None
