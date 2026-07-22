# Copyright (c) 2019-2026 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from urllib.parse import urlparse

from django.utils.module_loading import import_string

from tcms.testcases.models import BugSystem


def tracker_from_url(url, request):
    """
    Return the IssueTrackerType object for the system
    where ``base_url`` is part of ``url``. Usually we pass
    URLs to pre-existing defects to this method.
    """
    _in = urlparse(url)
    for bug_system in BugSystem.objects.all():
        _db = urlparse(bug_system.base_url)
        if (_in.scheme, _in.hostname, _in.port) == (
            _db.scheme,
            _db.hostname,
            _db.port,
        ) and _in.path.startswith(_db.path):
            return import_string(bug_system.tracker_type)(bug_system, request)

    return None
