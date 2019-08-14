# -*- coding: utf-8 -*-
"""
    Helper which facilitate actual communications with GitHub.
"""

import warnings
import threading


class GitHubThread(threading.Thread):
    """
        Execute GitHub RPC code in a thread!

        Executed from the IssueTracker interface methods.
    """

    def __init__(self, rpc, tracker, execution, bug_id):
        """
            @rpc - GitHub object
            @tracker - BugSystem object
            @execution - TestExecution object
            @bug_id - int
        """

        self.rpc = rpc
        self.execution = execution
        self.bug_id = bug_id

        repo_id = tracker.base_url.strip().strip('/').lower()
        repo_id = repo_id.replace('https://', '').replace('http://', '').replace('github.com/', '')
        self.repo = self.rpc.get_repo(repo_id)

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

            self.repo.get_issue(self.bug_id).create_comment(text)
        except Exception as err:  # pylint: disable=broad-except
            message = '%s: %s' % (err.__class__.__name__, err)
            warnings.warn(message)
