# -*- coding: utf-8 -*-
"""
    Helper which facilitate actual communications with JIRA.
"""

import warnings
import threading

from django.conf import settings
from django.core.urlresolvers import reverse


class JiraThread(threading.Thread):
    """
        Execute JIRA RPC code in a thread!

        Executed from the IssueTracker interface methods.
    """

    def __init__(self, rpc, testcase, bug):
        """
            @rpc - JIRA Python/RPC object
            @testcase - TestCase object
            @bug - TestCaseBug object
        """

        self.rpc = rpc
        self.testcase = testcase
        self.bug = bug
        super(JiraThread, self).__init__()

    def run(self):
        """
            Link the test case with the issue!
        """

        try:
            text = """---- Issue confirmed via test case ----
URL: %s
Summary: %s""" % (settings.KIWI_BASE_URL + reverse('testcases-get', args=[self.testcase.pk]),
                  self.testcase.summary)

            self.rpc.add_comment(self.bug.bug_id, text)
        except Exception, err:
            message = '%s: %s' % (err.__class__.__name__, err)
            warnings.warn(message)
