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

    def __init__(self, rpc, tracker, testcase, bug):
        """
            @rpc - Gitlab object
            @tracker - BugSystem object
            @testcase - TestCase object
            @bug - Bug object
        """

        self.rpc = rpc
        self.testcase = testcase
        self.bug = bug
        repo_id = '/'.join(tracker.base_url.strip().strip('/').split('/')[-2:])
        self.repo = self.rpc.projects.get(repo_id)

        super(GitlabThread, self).__init__()

    def run(self):
        """
            Link the test case with the issue!
        """

        try:
            text = """---- Issue confirmed via test case ----

URL: %s

Summary: %s""" % (self.testcase.get_full_url(), self.testcase.summary)

            self.repo.issues.get(self.bug.bug_id).notes.create(dict(body=text))
        except Exception as err:  # pylint: disable=broad-except
            message = '%s: %s' % (err.__class__.__name__, err)
            warnings.warn(message)
