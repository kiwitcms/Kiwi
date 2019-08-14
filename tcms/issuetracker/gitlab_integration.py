# -*- coding: utf-8 -*-
"""
    Helper which facilitates actual communications with GitLab.
"""

import warnings
import threading


class GitlabThread(threading.Thread):
    """
        Execute Gitlab RPC code in a thread!

        Executed from the IssueTracker interface methods.
    """

    def __init__(self, rpc, tracker, execution, bug_id):
        """
            @rpc - Gitlab object
            @tracker - BugSystem object
            @execution - TestExecution object
            @bug_id - int
        """

        self.rpc = rpc
        self.execution = execution
        self.bug_id = bug_id
        repo_id = '/'.join(tracker.base_url.strip().strip('/').split('/')[-2:])
        self.repo = self.rpc.projects.get(repo_id)

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

            self.repo.issues.get(self.bug_id).notes.create({'body': text})
        except Exception as err:  # pylint: disable=broad-except
            message = '%s: %s' % (err.__class__.__name__, err)
            warnings.warn(message)
