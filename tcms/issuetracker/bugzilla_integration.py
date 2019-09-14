# -*- coding: utf-8 -*-
"""
    Helper functions which facilitate actual communications with Bugzilla.
"""
from tcms.issuetracker.base import IntegrationThread


class BugzillaThread(IntegrationThread):
    """
        Execute Bugzilla RPC code in a thread!

        Executed from the IssueTracker interface methods.
    """
    def post_comment(self):
        self.rpc.update_bugs(self.bug_id, {'comment': {'comment': self.text(),
                                                       'is_private': False}})
