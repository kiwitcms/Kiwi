import re
import threading
import warnings

from opengraph.opengraph import OpenGraph

RE_ENDS_IN_INT = re.compile(r"[\d]+$")


class IntegrationThread(threading.Thread):
    """
    Used as a base class for everything else.
    """

    def __init__(self, rpc, bug_system, execution, bug_id):
        """
        :param rpc: Bug tracker RPC object
        :type rpc: object
        :param bug_system: BugSystem object
        :type bug_system: :class:`tcms.testcases.models.BugSystem`
        :param execution: TestExecution object
        :type execution: :class:`tcms.testruns.models.TestExecution`
        :param bug_id: Unique defect identifier in the system. Usually an int.
        :type bug_id: int or str
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
TE-%d: %s""" % (
            self.execution.run.pk,
            self.execution.run.summary,
            self.execution.run.get_full_url(),
            self.execution.pk,
            self.execution.case.summary,
        )

    def post_comment(self):
        raise NotImplementedError()

    def run(self):
        """
        Using RPC try to link the test case with existing bug!
        By default will post a comment!
        """

        try:
            self.post_comment()
        except Exception as err:  # pylint: disable=broad-except
            message = "%s: %s" % (err.__class__.__name__, err)
            warnings.warn(message)


class IssueTrackerType:
    """
    Represents actions which can be performed with issue trackers.
    This is a common interface for all issue trackers that Kiwi TCMS
    supports!
    """

    it_class = IntegrationThread
    rpc_cache = {}

    def __init__(self, bug_system, request):
        """
        :bug_system: - BugSystem object
        :request: - an HTTP request object
        """
        self.bug_system = bug_system
        self.request = request

    @classmethod
    def bug_id_from_url(cls, url):
        """
        Returns a unique identifier for reported defect. This is used by the
        underlying integration libraries. Usually that identifier is an
        integer number.

        The default implementation is to leave the last group of numeric
        characters at the end of a string!
        """
        return int(RE_ENDS_IN_INT.search(url.strip()).group(0))

    @staticmethod
    def get_case_components(case):
        """
        Returns a string that contains comma separated list of components
        bound to a given testcase
        """
        case_components = ", ".join(case.component.values_list("name", flat=True))
        return case_components

    def details(self, url):  # pylint: disable=no-self-use
        """
        Returns bug details to be used later. By default this method
        returns OpenGraph metadata (dict) which is shown in the UI as tooltips.
        You can override this method to provide different information.
        """
        result = OpenGraph(url, scrape=True)
        result["from_open_graph"] = True

        # remove data which we don't need
        for key in ["_url", "url", "scrape", "type"]:
            if key in result:
                del result[key]

        return result

    def _report_comment(self, execution):  # pylint: disable=no-self-use
        """
        Returns the comment which is used in the original defect report.
        """
        txt = execution.case.get_text_with_version(execution.case_text_version)

        comment = "Filed from execution %s\n\n" % execution.get_full_url()
        comment += "**Product:**\n%s\n\n" % execution.run.plan.product.name
        comment += "**Component(s):**\n%s\n\n" % self.get_case_components(
            execution.case
        )
        comment += "**Version-Release number** (if applicable):\n"
        comment += "%s\n\n" % execution.build.name
        comment += "**Steps to reproduce**: \n%s\n\n" % txt
        comment += "**Actual results**: \n<describe what happened>\n\n"

        return comment

    def report_issue_from_testexecution(self, execution, user):
        """
        When marking TestExecution results inside a Test Run there is a
        `Report` link. When the `Report` link is clicked this method is called
        to help the user report an issue in the IT.

        This is implemented by constructing an URL string which will pre-fill
        bug details like steps to reproduce, product, version, etc from the
        test case. Then we open this URL into another browser window!

        :execution: TestExecution object
        :user: User object
        :return: - string - URL
        """
        raise NotImplementedError()

    def add_testexecution_to_issue(self, executions, issue_url):
        """
        When linking defect URLs to Test Execution results there is a
        'Add comment to Issue tracker' checkbox. If
        selected this method is called. It should 'link' the existing
        defect back to the TE/TR which reproduced it.

        Usually this is implemented by adding a new comment pointing
        back to the TR/TE via the internal RPC object.

        :executions: - iterable of TestExecution objects
        :issue_url: - the URL of the existing defect
        """
        bug_id = self.bug_id_from_url(issue_url)
        for execution in executions:
            self.it_class(self.rpc, self.bug_system, execution, bug_id).start()

    def is_adding_testcase_to_issue_disabled(self):  # pylint: disable=invalid-name
        """
        When is linking a TC to a Bug report disabled?
        Usually when not all of the required credentials are provided.

        :return: True if bug system api url, username and password are provided
        :rtype: bool
        """
        return not (
            self.bug_system.api_url
            and self.bug_system.api_username
            and self.bug_system.api_password
        )

    def _rpc_connection(self):
        """
        Returns an object which is used to communicate to the external system.
        This method is meant to be overriden by inherited classes.
        """
        raise NotImplementedError()

    @property
    def rpc(self):
        """
        Returns an object which is used to communicate to the external system.
        This property is meant to be used by the rest of the integration code
        and provides caching b/c connecting to a remote system may be a slow
        operation.
        """
        # b/c jira.JIRA tries to connect when object is created
        # see https://github.com/kiwitcms/Kiwi/issues/100
        if self.is_adding_testcase_to_issue_disabled():
            return None

        if self.bug_system.base_url not in self.rpc_cache:
            self.rpc_cache[self.bug_system.base_url] = self._rpc_connection()

        return self.rpc_cache[self.bug_system.base_url]
