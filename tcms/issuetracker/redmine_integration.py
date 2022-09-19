# -*- coding: utf-8 -*-
"""
    Helper module which facilitate actual communications with Redmine.
"""
from tcms.issuetracker.base import IntegrationThread


class RedmineThread(IntegrationThread):
    """
    Execute Redmine REST API code in a thread!

    Executed from the IssueTracker interface methods.

    :meta private:
    """

    def post_comment(self):
        self.rpc.issue.get(self.bug_id).save(notes=self.text())
