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

    def __init__(self, rpc, tracker, testcase, bug):
        """
            @rpc - GitHub object
            @tracker - BugSystem object
            @testcase - TestCase object
            @bug - Bug object
        """

        self.rpc = rpc
        self.testcase = testcase
        self.bug = bug

        repo_id = tracker.base_url.strip().strip('/').lower()
        repo_id = repo_id.replace('https://', '').replace('http://', '').replace('github.com/', '')
        self.repo = self.rpc.get_repo(repo_id)

        super(GitHubThread, self).__init__()

    def run(self):
        """
            Link the test case with the issue!
        """

        try:
            text = """---- Issue confirmed via test case ----
URL: %s
Summary: %s""" % (self.testcase.get_full_url(), self.testcase.summary)

            self.repo.get_issue(int(self.bug.bug_id)).create_comment(text)
        except Exception as err:  # pylint: disable=broad-except
            message = '%s: %s' % (err.__class__.__name__, err)
            warnings.warn(message)
