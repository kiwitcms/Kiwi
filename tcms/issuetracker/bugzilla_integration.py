# -*- coding: utf-8 -*-
"""
    Helper functions which facilitate actual communications with Bugzilla.
"""

import warnings
import threading


class BugzillaThread(threading.Thread):
    """
        Execute Bugzilla RPC code in a thread!

        Executed from the IssueTracker interface methods.
    """

    def __init__(self, rpc, execution, bug_id):
        """
            @rpc - Bugzilla XML-RPC object
            @execution - TestExecution object
            @bug_id - int
        """

        self.rpc = rpc
        self.execution = execution
        self.bug_id = bug_id
        super().__init__()

    def run(self):
        """
            Using Bugzilla's XML-RPC try to link the test case with
            the bug!
        """

        try:
            text = """---- Confirmed via test execution ----
TR-%d: %s
%s
TE-%d: %s""" % (self.execution.run.pk,
                self.execution.run.summary,
                self.execution.run.get_full_url(),
                self.execution.pk,
                self.execution.case.summary)

            self.rpc.update_bugs(self.bug_id, {'comment': {'comment': text,
                                                           'is_private': False}})
        except Exception as err:  # pylint: disable=broad-except
            message = '%s: %s' % (err.__class__.__name__, err)
            warnings.warn(message)
