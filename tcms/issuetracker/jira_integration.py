# -*- coding: utf-8 -*-
"""
    Helper which facilitate actual communications with JIRA.
"""
from tcms.issuetracker.base import IntegrationThread


class JiraThread(IntegrationThread):
    """
    Execute JIRA RPC code in a thread!

    Executed from the IssueTracker interface methods.

    .. important::

        For configuration options see :class:`tcms.issuetracker.types.JIRA`!
    """

    def post_comment(self):
        self.rpc.add_comment(self.bug_id, self.text())
