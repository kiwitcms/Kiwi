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

    def __init__(self, rpc, execution, bug_id):
        """
            @rpc - Redmine Python/API object
            @execution - TestExecution object
            @bug - Bug object
        """
        self.rpc = rpc
        self.execution = execution
        self.bug_id = bug_id
        super().__init__()

    def run(self):
        """
            Link the test case with the issue!
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

            self.rpc.issue.get(self.bug.bug_id).save(notes=text)
        except Exception as err:  # pylint: disable=broad-except
            message = '%s: %s' % (err.__class__.__name__, err)
            warnings.warn(message)
