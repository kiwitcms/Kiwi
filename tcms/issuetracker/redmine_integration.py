# -*- coding: utf-8 -*-
"""
    Helper which facilitate actual communications with Redmine.
"""

import warnings
import threading


class RedmineThread(threading.Thread):
    """
        Execute Redmine REST API code in a thread!

        Executed from the IssueTracker interface methods.
    """

    def __init__(self, rpc, testcase, bug):
        """
            @rpc - Redmine Python/API object
            @testcase - TestCase object
            @bug - Bug object
        """

        self.rpc = rpc
        self.testcase = testcase
        self.bug = bug
        super().__init__()

    def run(self):
        """
            Link the test case with the issue!
        """

        try:
            text = """---- Issue confirmed via test case ----
URL: %s
Summary: %s""" % (self.testcase.get_full_url(), self.testcase.summary)

            self.rpc.issue.get(self.bug.bug_id).save(notes=text)
        except Exception as err:  # pylint: disable=broad-except
            message = '%s: %s' % (err.__class__.__name__, err)
            warnings.warn(message)
