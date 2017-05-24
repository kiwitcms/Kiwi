# -*- coding: utf-8 -*-
"""
    Helper functions which facilitate actual communications with Bugzilla.
"""

import warnings
import threading

from django.conf import settings
from django.core.urlresolvers import reverse

__all__ = ['add_bug_to_bugzilla']


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
Summary: %s""" % (settings.NITRATE_BASE_URL + reverse('tcms.testcases.views.get', args=[testcase.pk]),
                  testcase.summary)

        rpc.update_bugs(bug.bug_id, {'comment': {'comment': text, 'is_private': False}})
    except Exception, err:
        message = '%s: %s' % (err.__class__.__name__, err)
        warnings.warn(message)


class BugzillaThread(threading.Thread):
    """
        Execute Bugzilla RPC code in a thread if celery
        is not enabled.
    """

    def __init__(self, rpc, testcase, bug):
        self.rpc = rpc
        self.testcase = testcase
        self.bug = bug
        threading.Thread.__init__(self)

    def run(self):
        _rpc_add_bug_to_bugzilla(self.rpc, self.testcase, self.bug)


try:
    # todo: fix this or completely remove it
    # Adding test cases to Bugzilla currently breaks
    # when executed as Celery task, but not when executed
    # as a thread!!!
    _celery_add_bug_to_bugzilla = None

    # from celery import task

    # @task
    # def _celery_add_bug_to_bugzilla(rpc, testcase, bug):
    #     _rpc_add_bug_to_bugzilla(rpc, testcase, bug)
except ImportError:
    _celery_add_bug_to_bugzilla = None


def add_bug_to_bugzilla(rpc, testcase, bug):
    """
        Executed from the IssueTracker interface methods.
        This function takes care to run either in a thread or
        as a Celery task depending on how the settings are defined.

        NOTE: this is the only public function from this module!
    """
# todo: fix problem with celery, doesn't seem to work properly
# or maybe self.rpc doesn't get serialized very well ???
    if _celery_add_bug_to_bugzilla:
        _celery_add_bug_to_bugzilla.delay(rpc, testcase, bug)
    else:
        BugzillaThread(rpc, testcase, bug).start()
