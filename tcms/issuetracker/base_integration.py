# -*- coding: utf-8 -*-
import warnings
import threading


class IntegrationThread(threading.Thread):
    """
        Used as a base class for everything else.
    """

    def __init__(self, rpc, bug_system, execution, bug_id):
        """
            :param rpc: Bugzilla XML-RPC object
            :param bug_system: BugSystem object
            :param execution: TestExecution object
            :param bug_id: Unique defect identifier in the system. Usually an int.
        """
        self.rpc = rpc
        self.bug_system = bug_system
        self.execution = execution
        self.bug_id = bug_id

        super().__init__()

    def text(self):
        """
            Returns the text that will be posted as a comment to
            the reported bug!
        """
        return """---- Confirmed via test execution ----
TR-%d: %s
%s
TE-%d: %s""" % (self.execution.run.pk,
                self.execution.run.summary,
                self.execution.run.get_full_url(),
                self.execution.pk,
                self.execution.case.summary)

    def post_comment(self):
        raise NotImplementedError()

    def run(self):
        """
            Using Bugzilla's XML-RPC try to link the test case with
            the bug!
        """

        try:
            self.post_comment()
        except Exception as err:  # pylint: disable=broad-except
            message = '%s: %s' % (err.__class__.__name__, err)
            warnings.warn(message)
