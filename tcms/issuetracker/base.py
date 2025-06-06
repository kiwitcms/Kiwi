import re

from django.conf import settings
from django.utils.module_loading import import_string
from opengraph.opengraph import OpenGraph

RE_ENDS_IN_INT = re.compile(r"[\d]+$")


class IssueTrackerType:
    """
    Represents actions which can be performed with issue trackers.
    This is a common interface for all issue trackers that Kiwi TCMS
    supports!
    """

    def __init__(self, bug_system, request):
        """
        :bug_system: - BugSystem object
        :request: - an HTTP request object
        """
        self.bug_system = bug_system
        self.request = request

    @staticmethod
    def truncate(in_str, max_length):
        result = in_str

        if max_length < len(in_str):
            result = in_str[:max_length]
            result += "\n... truncated ..."

        return result

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
        for key in ["_url", "scrape", "type"]:
            if key in result:
                del result[key]

        if "id" not in result:
            result["id"] = self.bug_id_from_url(url)

        if "status" not in result:
            result["status"] = ""

        return result

    def _report_comment(
        self, execution, user=None, max_text_length=None
    ):  # pylint: disable=no-self-use
        """
        Returns the comment which is used in the original defect report.
        """
        txt = execution.case.get_text_with_version(execution.case_text_version)
        if max_text_length:
            txt = self.truncate(txt, max_text_length)

        reporter = "Unknown"
        if user:
            reporter = user.get_full_name() or user.username

        comment = f"""Filed from execution {execution.get_full_url()}

**Reporter:**
{reporter}

**Product:**
{execution.build.version.product.name}

**Version:**
{execution.build.version.value}

**Build:**
{execution.build.name}

**Component(s):**
{self.get_case_components(execution.case)}

**Steps to reproduce**:
{txt}

**Actual results**:
<describe what happened>


"""
        return comment

    def _report_issue(self, execution, user):
        """
        Used internally to perform the actual report! If you want to override behavior
        this is the appropriate method!

        :return: (object, str) - returns the newly created issue represented as
                 an object that is understood by the internal RPC integration code
                 and the URL to the newly created issue.
        """
        raise NotImplementedError()

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
        (new_issue, url) = self._report_issue(execution, user)
        if new_issue:
            self.post_process_new_issue(new_issue, execution, user)
        return url

    def post_process_new_issue(self, new_issue, execution, user):
        """
        Perform any post-processing for newly created issues.

        :new_issue: An object specific to the actual RPC implementation
        :execution: TestExecution object
        :user: User object

        .. versionadded:: 11.4
        """
        for fully_qualified_dotted_path in settings.EXTERNAL_ISSUE_POST_PROCESSORS:
            processor_function = import_string(fully_qualified_dotted_path)
            processor_function(self.rpc, new_issue, execution, user)

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
            self.post_comment(execution, bug_id)

    @staticmethod
    def text(execution):
        """
        Returns the text that will be posted as a comment to
        the reported bug!
        """
        return f"""---- Confirmed via test execution ----
TR-{execution.run.pk}: {execution.run.summary}
{execution.run.get_full_url()}
TE-{execution.pk}: {execution.case.summary}"""

    def post_comment(self, execution, bug_id):
        """
        :param execution: TestExecution object
        :type execution: :class:`tcms.testruns.models.TestExecution`
        :param bug_id: Unique defect identifier in the system. Usually an int.
        :type bug_id: int or str
        """
        raise NotImplementedError()

    def is_adding_testcase_to_issue_disabled(self):  # pylint: disable=invalid-name
        """
        When is linking a TC to a Bug report disabled?
        Usually when not all of the required credentials are provided.

        :return: True if bug system api url, username and password are provided
        :rtype: bool
        """
        (api_username, api_password) = self.rpc_credentials

        return not (self.bug_system.api_url and api_username and api_password)

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
        This property is meant to be used by the rest of the integration code.
        """
        # b/c jira.JIRA tries to connect when object is created
        # see https://github.com/kiwitcms/Kiwi/issues/100
        if self.is_adding_testcase_to_issue_disabled():
            return None

        return self._rpc_connection()

    @property
    def rpc_credentials(self):
        """
        Returns an tuple of (api_username, api_token_or_password) meant for connecting
        to a 3rd party issue tracker system.

        It can be overriden in order to provide more flexible integrations!

        .. versionadded:: 12.6
        """
        if settings.EXTERNAL_ISSUE_RPC_CREDENTIALS:
            credentials_function = import_string(
                settings.EXTERNAL_ISSUE_RPC_CREDENTIALS
            )
            result = credentials_function(self)

            # if result is None or not a tuple then fallback
            if result and isinstance(result, tuple):
                return result

        return (self.bug_system.api_username, self.bug_system.api_password)
