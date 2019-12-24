"""
    This module implements Kiwi TCMS interface to external issue tracking systems.
    Refer to each implementor class for integration specifics!
"""

import os
import tempfile
from urllib.parse import quote, urlencode

import bugzilla
import github
import gitlab
import jira
import redminelib
from django.conf import settings

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.issuetracker import (bugzilla_integration, github_integration,
                               gitlab_integration, jira_integration,
                               redmine_integration)
from tcms.issuetracker.base import IssueTrackerType
from tcms.issuetracker.kiwitcms import KiwiTCMS  # noqa, pylint: disable=unused-import


def from_name(name):
    """
        Return the class which matches ``name`` if it exists inside this
        module or raise an exception.
    """
    if name not in globals():
        raise NotImplementedError('IT of type %s is not supported' % name)
    return globals()[name]


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

    def __init__(self, bug_system):
        super().__init__(bug_system)

        # directory for Bugzilla credentials
        self._bugzilla_cache_dir = getattr(
            settings,
            "BUGZILLA_AUTH_CACHE_DIR",
            tempfile.mkdtemp(prefix='.bugzilla-')
        )

    def _rpc_connection(self):
        if not os.path.exists(self._bugzilla_cache_dir):
            os.makedirs(self._bugzilla_cache_dir, 0o700)

        return bugzilla.Bugzilla(
            self.bug_system.api_url,
            user=self.bug_system.api_username,
            password=self.bug_system.api_password,
            cookiefile=self._bugzilla_cache_dir + 'cookie',
            tokenfile=self._bugzilla_cache_dir + 'token',
        )

    def add_testexecution_to_issue(self, executions, issue_url):
        bug_id = self.bug_id_from_url(issue_url)
        for execution in executions:
            bugzilla_integration.BugzillaThread(self.rpc,
                                                self.bug_system,
                                                execution,
                                                bug_id).start()

    def report_issue_from_testexecution(self, execution, user):
        args = {}
        args['cf_build_id'] = execution.run.build.name

        args['comment'] = self._report_comment(execution)
        args['component'] = execution.case.component.values_list('name',
                                                                 flat=True)
        args['product'] = execution.run.plan.product.name
        args['short_desc'] = 'Test case failure: %s' % execution.case.summary
        args['version'] = execution.run.product_version

        url = self.bug_system.base_url
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

    def _rpc_connection(self):
        if hasattr(settings, 'JIRA_OPTIONS'):
            options = settings.JIRA_OPTIONS
        else:
            options = None

        return jira.JIRA(
            self.bug_system.api_url,
            basic_auth=(self.bug_system.api_username, self.bug_system.api_password),
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
            jira_integration.JiraThread(self.rpc, self.bug_system, execution, bug_id).start()

    def report_issue_from_testexecution(self, execution, user):
        """
            For the HTML API description see:
            https://confluence.atlassian.com/display/JIRA050/Creating+Issues+via+direct+HTML+links
        """
        # note: your jira instance needs to have the same projects
        # defined otherwise this will fail!
        project = self.rpc.project(execution.run.plan.product.name)

        try:
            issue_type = self.rpc.issue_type_by_name('Bug')
        except KeyError:
            issue_type = self.rpc.issue_types()[0]

        args = {
            'pid': project.id,
            'issuetype': issue_type.id,
            'summary': 'Failed test: %s' % execution.case.summary,
        }

        try:
            # apparently JIRA can't search users via their e-mail so try to
            # search by username and hope that it matches
            tested_by = execution.tested_by
            if not tested_by:
                tested_by = execution.assignee

            args['reporter'] = self.rpc.user(tested_by.username).key
        except jira.JIRAError:
            pass

        args['description'] = self._report_comment(execution)

        url = self.bug_system.base_url
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

    def _rpc_connection(self):
        # NOTE: we use an access token so only the password field is required
        return github.Github(self.bug_system.api_password)

    def add_testexecution_to_issue(self, executions, issue_url):
        bug_id = self.bug_id_from_url(issue_url)
        for execution in executions:
            github_integration.GitHubThread(self.rpc, self.bug_system, execution, bug_id).start()

    def is_adding_testcase_to_issue_disabled(self):
        return not (self.bug_system.base_url and self.bug_system.api_password)

    def report_issue_from_testexecution(self, execution, user):
        """
            GitHub only supports title and body parameters
        """
        args = {
            'title': 'Failed test: %s' % execution.case.summary,
            'body': self._report_comment(execution),
        }

        try:
            repo_id = github_integration.GitHubThread.repo_id(self.bug_system)
            repo = self.rpc.get_repo(repo_id)
            issue = repo.create_issue(**args)

            # add a link reference that will be shown in the UI
            LinkReference.objects.get_or_create(
                execution=execution,
                url=issue.html_url,
                is_defect=True,
            )

            return issue.html_url
        except Exception:  # pylint: disable=broad-except
            # something above didn't work so return a link for manually
            # entering issue details with info pre-filled
            url = self.bug_system.base_url
            if not url.endswith('/'):
                url += '/'

            return url + '/issues/new?' + urlencode(args, True)


class Gitlab(IssueTrackerType):
    """
        Support for Gitlab. Requires:

        :base_url: URL to a GitLab repository for which we're going to report issues
        :api_url: URL to GitLab instance. Usually gitlab.com!
        :api_password: GitLab API token.

        .. note::

            You can leave ``api_username`` field blank because
            the integration code doesn't use it!
    """

    def _rpc_connection(self):
        # we use an access token so only the password field is required
        return gitlab.Gitlab(self.bug_system.api_url,
                             private_token=self.bug_system.api_password)

    def add_testexecution_to_issue(self, executions, issue_url):
        bug_id = self.bug_id_from_url(issue_url)
        for execution in executions:
            gitlab_integration.GitlabThread(self.rpc, self.bug_system, execution, bug_id).start()

    def is_adding_testcase_to_issue_disabled(self):
        return not (self.bug_system.api_url and self.bug_system.api_password)

    def report_issue_from_testexecution(self, execution, user):
        args = {
            'issue[title]': 'Failed test: %s' % execution.case.summary,
            'issue[description]': self._report_comment(execution),
        }

        url = self.bug_system.base_url
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

    def _rpc_connection(self):
        return redminelib.Redmine(
            self.bug_system.api_url,
            username=self.bug_system.api_username,
            password=self.bug_system.api_password
        )

    def add_testexecution_to_issue(self, executions, issue_url):
        bug_id = self.bug_id_from_url(issue_url)
        for execution in executions:
            redmine_integration.RedmineThread(self.rpc,
                                              self.bug_system,
                                              execution,
                                              bug_id).start()

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

    def report_issue_from_testexecution(self, execution, user):
        project = self.find_project_by_name(execution.run.plan.product.name)

        issue_type = self.find_issue_type_by_name(project, 'Bug')

        query = "issue[tracker_id]=" + str(issue_type.id)
        query += "&issue[subject]=" + quote('Failed test: %s' % execution.case.summary)

        comment = self._report_comment(execution)
        query += "&issue[description]=%s" % quote(comment)

        url = self.bug_system.base_url
        if not url.endswith('/'):
            url += '/'

        return url + '/projects/%s/issues/new?' % project.id + query
