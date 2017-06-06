# -*- coding: utf-8 -*-
"""
    Helper functions which facilitate actual communications with Bugzilla.
"""

import warnings
import threading

from django.conf import settings
from django.core.urlresolvers import reverse

__all__ = ['BugzillaThread']


def _rpc_add_bug_to_bugzilla(rpc, testcase, bug):
    """
        Using Bugzilla's XML-RPC try to link the test case with
        the bug!

        @rpc - Bugzilla XML-RPC object
        @testcase - TestCase object
        @bug - TestCaseBug object
    """

    try:
        text = """---- Bug confirmed via test case ----
URL: %s
Summary: %s""" % (settings.KIWI_BASE_URL + reverse('testcases-get', args=[testcase.pk]),
                  testcase.summary)

        rpc.update_bugs(bug.bug_id, {'comment': {'comment': text, 'is_private': False}})
    except Exception, err:
        message = '%s: %s' % (err.__class__.__name__, err)
        warnings.warn(message)


class BugzillaThread(threading.Thread):
    """
        Execute Bugzilla RPC code in a thread!

        Executed from the IssueTracker interface methods.
    """

    def __init__(self, rpc, testcase, bug):
        self.rpc = rpc
        self.testcase = testcase
        self.bug = bug
        threading.Thread.__init__(self)

    def run(self):
        _rpc_add_bug_to_bugzilla(self.rpc, self.testcase, self.bug)
