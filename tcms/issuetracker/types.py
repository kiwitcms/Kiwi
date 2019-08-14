"""
    This module implements Kiwi TCMS interface to external issue tracking systems.
    :class:`tcms.issuetracker.types.IssueTrackerType` provides the interface
    while the rest of the classes in this module implement it! Refer to each
    implementor class for integration specifics!
"""

import os
import re
import tempfile
from urllib.parse import urlencode, quote

import jira
import github
import bugzilla
import gitlab
import redminelib

from django.conf import settings

from tcms.issuetracker import bugzilla_integration
from tcms.issuetracker import jira_integration
from tcms.issuetracker import github_integration
from tcms.issuetracker import gitlab_integration
from tcms.issuetracker import redmine_integration


RE_ENDS_IN_INT = re.compile(r'[\d]+$')


class IssueTrackerType:
    """
        Represents actions which can be performed with issue trackers.
        This is a common interface for all issue trackers that Kiwi TCMS
        supports!
    """

    def __init__(self, tracker):
        """
            :tracker: - BugSystem object
        """
        self.tracker = tracker

    @classmethod
    def from_name(cls, name):
        """
            Return the class which matches ``name`` if it exists inside this
            module or raise an exception.
        """
        if name not in globals():
            raise NotImplementedError('IT of type %s is not supported' % name)
        return globals()[name]

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

    def report_issue_from_testcase(self, caserun):
        """
            When marking Test Case results inside a Test Run there is a
            `Report` link. When the `Report` link is clicked this method is called
            to help the user report an issue in the IT.

            This is implemented by constructing an URL string which will pre-fill
            bug details like steps to reproduce, product, version, etc from the
            test case. Then we open this URL into another browser window!

            :caserun: - TestExecution object
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
        raise NotImplementedError()

    def is_adding_testcase_to_issue_disabled(self):  # pylint: disable=invalid-name, no-self-use
        """
            When is linking a TC to a Bug report disabled?
            Usually when all the required credentials are provided.

            :return: - boolean
        """
        return not (self.tracker.api_url
                    and self.tracker.api_username
                    and self.tracker.api_password)


class Bugzilla(IssueTrackerType):
    """
        Support for Bugzilla. Requires:

        :api_url: - the XML-RPC URL for your Bugzilla instance
        :api_username: - a username registered in Bugzilla
        :api_password: - the password for this username

        You can also provide the ``BUGZILLA_AUTH_CACHE_DIR`` setting (in ``product.py``)
        to control where authentication cookies for Bugzilla will be saved. If this
        is not provided a temporary directory will be used each time we try to login
        into Bugzilla!
    """

    def __init__(self, tracker):
        super().__init__(tracker)

        # directory for Bugzilla credentials
        self._bugzilla_cache_dir = getattr(
            settings,
            "BUGZILLA_AUTH_CACHE_DIR",
            tempfile.mkdtemp(prefix='.bugzilla-')
        )
        if not os.path.exists(self._bugzilla_cache_dir):
            os.makedirs(self._bugzilla_cache_dir, 0o700)

        self._rpc = None

    @property
    def rpc(self):
        if self._rpc is None:
            self._rpc = bugzilla.Bugzilla(
                self.tracker.api_url,
                user=self.tracker.api_username,
                password=self.tracker.api_password,
                cookiefile=self._bugzilla_cache_dir + 'cookie',
                tokenfile=self._bugzilla_cache_dir + 'token',
            )
        return self._rpc

    def add_testexecution_to_issue(self, executions, issue_url):
        bug_id = self.bug_id_from_url(issue_url)
        for execution in executions:
            bugzilla_integration.BugzillaThread(self.rpc, execution, bug_id).start()

    def report_issue_from_testcase(self, caserun):
        args = {}
        args['cf_build_id'] = caserun.run.build.name

        txt = caserun.case.get_text_with_version(case_text_version=caserun.case_text_version)

        comment = "Filed from caserun %s\n\n" % caserun.get_full_url()
        comment += "Version-Release number of selected " \
                   "component (if applicable):\n"
        comment += '%s\n\n' % caserun.build.name
        comment += "Steps to Reproduce: \n%s\n\n" % txt
        comment += "Actual results: \n<describe what happened>\n\n"

        args['comment'] = comment
        args['component'] = caserun.case.component.values_list('name',
                                                               flat=True)
        args['product'] = caserun.run.plan.product.name
        args['short_desc'] = 'Test case failure: %s' % caserun.case.summary
        args['version'] = caserun.run.product_version

        url = self.tracker.base_url
        if not url.endswith('/'):
            url += '/'

        return url + 'enter_bug.cgi?' + urlencode(args, True)


class JIRA(IssueTrackerType):
    """
        Support for JIRA. Requires:

        :api_url: - the API URL for your JIRA instance
        :api_username: - a username registered in JIRA
        :api_password: - the password for this username

        Additional control can be applied via the ``JIRA_OPTIONS`` configuration
        setting (in ``product.py``). By default this setting is not provided and
        the code uses ``jira.JIRA.DEFAULT_OPTIONS`` from the ``jira`` Python module!
    """

    def __init__(self, tracker):
        super().__init__(tracker)

        if hasattr(settings, 'JIRA_OPTIONS'):
            options = settings.JIRA_OPTIONS
        else:
            options = None

        # b/c jira.JIRA tries to connect when object is created
        # see https://github.com/kiwitcms/Kiwi/issues/100
        if not self.is_adding_testcase_to_issue_disabled():
            self.rpc = jira.JIRA(
                tracker.api_url,
                basic_auth=(self.tracker.api_username, self.tracker.api_password),
                options=options,
            )

    @classmethod
    def bug_id_from_url(cls, url):
        """
            Jira IDs are the last group of chars at the end of the URL.
            For example https://issues.jenkins-ci.org/browse/JENKINS-31044
        """
        return url.strip().split('/')[-1]

    def add_testexecution_to_issue(self, executions, issue_url):
        bug_id = self.bug_id_from_url(issue_url)
        for execution in executions:
            jira_integration.JiraThread(self.rpc, execution, bug_id).start()

    def report_issue_from_testcase(self, caserun):
        """
            For the HTML API description see:
            https://confluence.atlassian.com/display/JIRA050/Creating+Issues+via+direct+HTML+links
        """
        # note: your jira instance needs to have the same projects
        # defined otherwise this will fail!
        project = self.rpc.project(caserun.run.plan.product.name)

        try:
            issue_type = self.rpc.issue_type_by_name('Bug')
        except KeyError:
            issue_type = self.rpc.issue_types()[0]

        args = {
            'pid': project.id,
            'issuetype': issue_type.id,
            'summary': 'Failed test: %s' % caserun.case.summary,
        }

        try:
            # apparently JIRA can't search users via their e-mail so try to
            # search by username and hope that it matches
            tested_by = caserun.tested_by
            if not tested_by:
                tested_by = caserun.assignee

            args['reporter'] = self.rpc.user(tested_by.username).key
        except jira.JIRAError:
            pass

        txt = caserun.case.get_text_with_version(case_text_version=caserun.case_text_version)

        comment = "Filed from caserun %s\n\n" % caserun.get_full_url()
        comment += "Product:\n%s\n\n" % caserun.run.plan.product.name
        comment += "Component(s):\n%s\n\n" % caserun.case.component.values_list('name', flat=True)
        comment += "Version-Release number of selected " \
                   "component (if applicable):\n"
        comment += "%s\n\n" % caserun.build.name
        comment += "Steps to Reproduce: \n%s\n\n" % txt
        comment += "Actual results: \n<describe what happened>\n\n"
        args['description'] = comment

        url = self.tracker.base_url
        if not url.endswith('/'):
            url += '/'

        return url + '/secure/CreateIssueDetails!init.jspa?' + urlencode(args, True)


class GitHub(IssueTrackerType):
    """
        Support for GitHub. Requires:

        :base_url: - URL to a GitHub repository for which we're going to report issues
        :api_password: - GitHub API token.

        .. note::

            You can leave the ``api_url`` and ``api_username`` fields blank because
            the integration code doesn't use them!
    """

    def __init__(self, tracker):
        super().__init__(tracker)

        # NOTE: we use an access token so only the password field is required
        self.rpc = github.Github(self.tracker.api_password)

    def add_testexecution_to_issue(self, executions, issue_url):
        bug_id = self.bug_id_from_url(issue_url)
        for execution in executions:
            github_integration.GitHubThread(self.rpc, self.tracker, execution, bug_id).start()

    def is_adding_testcase_to_issue_disabled(self):
        return not (self.tracker.base_url and self.tracker.api_password)

    def report_issue_from_testcase(self, caserun):
        """
            GitHub only supports title and body parameters
        """
        args = {
            'title': 'Failed test: %s' % caserun.case.summary,
        }

        txt = caserun.case.get_text_with_version(case_text_version=caserun.case_text_version)

        comment = "Filed from caserun %s\n\n" % caserun.get_full_url()
        comment += "Product:\n%s\n\n" % caserun.run.plan.product.name
        comment += "Component(s):\n%s\n\n" % caserun.case.component.values_list('name', flat=True)
        comment += "Version-Release number of selected " \
                   "component (if applicable):\n"
        comment += "%s\n\n" % caserun.build.name
        comment += "Steps to Reproduce: \n%s\n\n" % txt
        comment += "Actual results: \n<describe what happened>\n\n"
        args['body'] = comment

        url = self.tracker.base_url
        if not url.endswith('/'):
            url += '/'

        return url + '/issues/new?' + urlencode(args, True)


class Gitlab(IssueTrackerType):
    """
        Support for Gitlab. Requires:

        :base_url: - URL to a Gitlab repository for which we're going to report issues
        :api_url: - URL to GitLab instance. Usually gitlab.com!
        :api_password: - Gitlab API token.
    """

    def __init__(self, tracker):
        super().__init__(tracker)

        # we use an access token so only the password field is required
        self.rpc = gitlab.Gitlab(self.tracker.api_url, private_token=self.tracker.api_password)

    def add_testexecution_to_issue(self, executions, issue_url):
        bug_id = self.bug_id_from_url(issue_url)
        for execution in executions:
            gitlab_integration.GitlabThread(self.rpc, self.tracker, execution, bug_id).start()

    def is_adding_testcase_to_issue_disabled(self):
        return not (self.tracker.base_url and self.tracker.api_password)

    def report_issue_from_testcase(self, caserun):
        args = {
            'issue[title]': 'Failed test: %s' % caserun.case.summary,
        }

        txt = caserun.case.get_text_with_version(case_text_version=caserun.case_text_version)

        comment = "Filed from caserun %s\n\n" % caserun.get_full_url()
        comment += "**Product**:\n%s\n\n" % caserun.run.plan.product.name
        comment += "**Component(s)**:\n%s\n\n"\
                   % caserun.case.component.values_list('name', flat=True)
        comment += "Version-Release number of selected " \
                   "component (if applicable):\n"
        comment += "%s\n\n" % caserun.build.name
        comment += "**Steps to Reproduce**: \n%s\n\n" % txt
        comment += "**Actual results**: \n<describe what happened>\n\n"
        args['issue[description]'] = comment

        url = self.tracker.base_url
        if not url.endswith('/'):
            url += '/'

        return url + '/issues/new?' + urlencode(args, True)


class Redmine(IssueTrackerType):
    """
        Support for Redmine. Requires:

        :api_url: - the API URL for your Redmine instance
        :api_username: - a username registered in Redmine
        :api_password: - the password for this username
    """

    def __init__(self, tracker):
        super().__init__(tracker)

        if not self.is_adding_testcase_to_issue_disabled():
            self.rpc = redminelib.Redmine(
                self.tracker.api_url,
                username=self.tracker.api_username,
                password=self.tracker.api_password
            )

    def add_testexecution_to_issue(self, executions, issue_url):
        bug_id = self.bug_id_from_url(issue_url)
        for execution in executions:
            redmine_integration.RedmineThread(self.rpc, execution, bug_id).start()

    def find_project_by_name(self, name):
        """
            Return a Redmine project which matches the given product name.

            .. note::

                If there is no match then return the first project in Redmine.
        """
        try:
            return self.rpc.project.get(name)
        except redminelib.exceptions.ResourceNotFoundError:
            projects = self.rpc.project.all()
            return projects[0]

    @staticmethod
    def find_issue_type_by_name(project, name):
        """
            Return a Redmine tracker matching name ('Bug').

            .. note::

                If there is no match then return the first one!
        """
        for trk in project.trackers:
            if str(trk).lower() == name.lower():
                return trk

        return project.trackers[0]

    def report_issue_from_testcase(self, caserun):
        project = self.find_project_by_name(caserun.run.plan.product.name)

        issue_type = self.find_issue_type_by_name(project, 'Bug')

        query = "issue[tracker_id]=" + str(issue_type.id)
        query += "&issue[subject]=" + quote('Failed test:{0}'.format(caserun.case.summary))

        txt = caserun.case.get_text_with_version(case_text_version=caserun.case_text_version)

        comment = "Filed from caserun %s\n\n" % caserun.get_full_url()
        comment += "Product:\n%s\n\n" % caserun.run.plan.product.name
        comment += "Component(s):\n%s\n\n" % caserun.case.component.values_list('name', flat=True)
        comment += "Version-Release number of selected " \
                   "component (if applicable):\n"
        comment += "%s\n\n" % caserun.build.name
        comment += "Steps to Reproduce: \n%s\n\n" % txt
        comment += "Actual results: \n<describe what happened>\n\n"

        query += "&issue[description]={0}".format(quote(comment))

        url = self.tracker.base_url
        if not url.endswith('/'):
            url += '/'

        return url + '/projects/{0}/issues/new?'.format(str(project.id)) + query
