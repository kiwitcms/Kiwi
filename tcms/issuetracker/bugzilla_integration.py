# -*- coding: utf-8 -*-
"""
    Helper functions which facilitate actual communications with Bugzilla.
"""

import warnings
import threading
import xmlrpclib

__all__ = ['add_bug_to_bugzilla']


def _rpc_add_bug_to_bugzilla(bugzilla, testcase, bug):
    """
        Using Bugzilla's XML-RPC try to link the test case with
        the bug!

        @bugzilla - TestCaseBugSystem object
        @testcase - TestCase object
        @bug - TestCaseBug object
    """

    try:
        proxy = xmlrpclib.ServerProxy(bugzilla.api_endpoint)
        proxy.ExternalBugs.add_external_bug({
            'Bugzilla_login': bugzilla.api_username,
            'Bugzilla_password': bugzilla.api_password,
            'bug_ids': [bug.pk, ],
            'external_bugs': [
                {'ext_bz_bug_id': str(testcase.pk),
                 'ext_type_description': testcase.summary}, ]
        })
    except Exception, err:
        message = '%s: %s' % (err.__class__.__name__, err)
        warnings.warn(message)


class BugzillaThread(threading.Thread):
    """
        Execute Bugzilla RPC code in a thread if celery
        is not enabled.
    """

    def __init__(self, bugzilla, testcase, bug):
        self.bugzilla = bugzilla
        self.testcase = testcase
        self.bug = bug
        threading.Thread.__init__(self)

    def run(self):
        _rpc_add_bug_to_bugzilla(self.bugzilla, self.testcase, self.bug)


try:
    from celery import task

    @task
    def _celery_add_bug_to_bugzilla(bugzilla, testcase, bug):
        _rpc_add_bug_to_bugzilla(bugzilla, testcase, bug)
except ImportError:
    _celery_add_bug_to_bugzilla = None


def add_bug_to_bugzilla(bugzilla, testcase, bug):
    """
        Executed from the IssueTracker interface methods.
        This function takes care to run either in a thread or
        as a Celery task depending on how the settings are defined.

        NOTE: this is the only public function from this module!
    """

    if _celery_add_bug_to_bugzilla:
        _celery_add_bug_to_bugzilla.delay(bugzilla, testcase, bug)
    else:
        BugzillaThread(bugzilla, testcase, bug).start()
