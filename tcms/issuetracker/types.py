"""
    This module implements Kiwi TCMS interface to external issue tracking systems.
    Refer to each implementor class for integration specifics!
"""

from urllib.parse import urlencode

import github
import gitlab
import jira
import redminelib
from django.conf import settings

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.issuetracker import (
    github_integration,
    gitlab_integration,
    jira_integration,
    redmine_integration,
)
from tcms.issuetracker.base import IssueTrackerType
from tcms.issuetracker.bugzilla_integration import (  # noqa, pylint: disable=unused-import
    Bugzilla,
)

# conditional import b/c this App can be disabled
if "tcms.bugs.apps.AppConfig" in settings.INSTALLED_APPS:
    from tcms.issuetracker.kiwitcms import (  # noqa, pylint: disable=unused-import
        KiwiTCMS,
    )


class JIRA(IssueTrackerType):
    """
    Support for JIRA. Requires:

    :base_url: - the URL of this JIRA instance
    :api_username: - a username registered in JIRA
    :api_password: - the password for this username

    Additional control can be applied via the ``JIRA_OPTIONS`` configuration
    setting (in ``product.py``). By default this setting is not provided and
    the code uses ``jira.JIRA.DEFAULT_OPTIONS`` from the ``jira`` Python module!
    """

    it_class = jira_integration.JiraThread

    def _rpc_connection(self):
        if hasattr(settings, "JIRA_OPTIONS"):
            options = settings.JIRA_OPTIONS
        else:
            options = None

        return jira.JIRA(
            self.bug_system.base_url,
            basic_auth=(self.bug_system.api_username, self.bug_system.api_password),
            options=options,
        )

    def is_adding_testcase_to_issue_disabled(self):
        return not (
            self.bug_system.base_url
            and self.bug_system.api_username
            and self.bug_system.api_password
        )

    @classmethod
    def bug_id_from_url(cls, url):
        """
        Jira IDs are the last group of chars at the end of the URL.
        For example https://issues.jenkins-ci.org/browse/JENKINS-31044
        """
        return url.strip().split("/")[-1]

    def details(self, url):
        try:
            issue = self.rpc.issue(self.bug_id_from_url(url))
            return {
                "title": issue.fields.summary,
                "description": issue.fields.description,
            }
        except jira.exceptions.JIRAError:
            return super().details(url)

    def report_issue_from_testexecution(self, execution, user):
        """
        JIRA Project == Kiwi TCMS Product, otherwise defaults to the first found
        Issue Type == Bug or the first one found

        If 1-click bug report doesn't work then fall back to manual
        reporting!

        For the HTML API description see:
        https://confluence.atlassian.com/display/JIRA050/Creating+Issues+via+direct+HTML+links
        """
        try:
            project = self.rpc.project(execution.run.plan.product.name)
        except jira.exceptions.JIRAError:
            project = self.rpc.projects()[0]

        try:
            issue_type = self.rpc.issue_type_by_name("Bug")
        except KeyError:
            issue_type = self.rpc.issue_types()[0]

        try:
            new_issue = self.rpc.create_issue(
                project=project.id,
                issuetype={"name": issue_type.name},
                summary="Failed test: %s" % execution.case.summary,
                description=self._report_comment(execution),
            )
            new_url = self.bug_system.base_url + "/browse/" + new_issue.key

            # add a link reference that will be shown in the UI
            LinkReference.objects.get_or_create(
                execution=execution,
                url=new_url,
                is_defect=True,
            )

            return new_url
        except jira.exceptions.JIRAError:
            pass

        args = {
            "pid": project.id,
            "issuetype": issue_type.id,
            "summary": "Failed test: %s" % execution.case.summary,
            "description": self._report_comment(execution),
        }

        url = self.bug_system.base_url
        if not url.endswith("/"):
            url += "/"

        return url + "/secure/CreateIssueDetails!init.jspa?" + urlencode(args, True)


class GitHub(IssueTrackerType):
    """
    Support for GitHub. Requires:

    :base_url: - URL to a GitHub repository for which we're going to report issues
    :api_password: - GitHub API token - needs ``repo`` or ``public_repo``
                     permissions.

    .. note::

        You can leave the ``api_url`` and ``api_username`` fields blank because
        the integration code doesn't use them!
    """

    it_class = github_integration.GitHubThread

    def _rpc_connection(self):
        # NOTE: we use an access token so only the password field is required
        return github.Github(self.bug_system.api_password)

    def is_adding_testcase_to_issue_disabled(self):
        return not (self.bug_system.base_url and self.bug_system.api_password)

    def report_issue_from_testexecution(self, execution, user):
        """
        GitHub only supports title and body parameters
        """
        args = {
            "title": "Failed test: %s" % execution.case.summary,
            "body": self._report_comment(execution),
        }

        try:
            repo_id = self.it_class.repo_id(self.bug_system)
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
            if not url.endswith("/"):
                url += "/"

            return url + "/issues/new?" + urlencode(args, True)

    def details(self, url):
        """
        Use GitHub's API instead of OpenGraph to return bug
        details b/c it will work for both public and private URLs.
        """
        repo_id = self.it_class.repo_id(self.bug_system)
        repo = self.rpc.get_repo(repo_id)
        issue = repo.get_issue(self.bug_id_from_url(url))
        return {
            "title": issue.title,
            "description": issue.body,
        }


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

    it_class = gitlab_integration.GitlabThread

    def _rpc_connection(self):
        # we use an access token so only the password field is required
        return gitlab.Gitlab(
            self.bug_system.api_url, private_token=self.bug_system.api_password
        )

    def is_adding_testcase_to_issue_disabled(self):
        return not (self.bug_system.api_url and self.bug_system.api_password)

    def report_issue_from_testexecution(self, execution, user):
        repo_id = self.it_class.repo_id(self.bug_system)
        project = self.rpc.projects.get(repo_id)
        new_issue = project.issues.create(
            {
                "title": "Failed test: %s" % execution.case.summary,
                "description": self._report_comment(execution),
            }
        )

        # and also add a link reference that will be shown in the UI
        LinkReference.objects.get_or_create(
            execution=execution,
            url=new_issue.attributes["web_url"],
            is_defect=True,
        )
        return new_issue.attributes["web_url"]

    def details(self, url):
        """
        Use Gitlab API instead of OpenGraph to return bug
        details b/c it will work for both public and private URLs.
        """
        repo_id = self.it_class.repo_id(self.bug_system)
        project = self.rpc.projects.get(repo_id)
        issue = project.issues.get(self.bug_id_from_url(url))
        return {
            "title": issue.title,
            "description": issue.description,
        }


class Redmine(IssueTrackerType):
    """
    Support for Redmine. Requires:

    :base_url: - the URL for this Redmine instance
    :api_username: - a username registered in Redmine
    :api_password: - the password for this username
    """

    it_class = redmine_integration.RedmineThread

    def is_adding_testcase_to_issue_disabled(self):
        return not (
            self.bug_system.base_url
            and self.bug_system.api_username
            and self.bug_system.api_password
        )

    def _rpc_connection(self):
        return redminelib.Redmine(
            self.bug_system.base_url,
            username=self.bug_system.api_username,
            password=self.bug_system.api_password,
        )

    def details(self, url):
        try:
            issue = self.rpc.issue.get(self.bug_id_from_url(url))
            return {
                "title": issue.subject,
                "description": issue.description,
            }
        except redminelib.exceptions.ResourceNotFoundError:
            return super().details(url)

    def redmine_project_by_name(self, name):
        """
        Return a Redmine project which matches the given product name.
        If there is no match then return the first project in Redmine!
        """
        all_projects = self.rpc.project.all()
        for project in all_projects:
            if project.name == name:
                return project

        return all_projects[0]

    @staticmethod
    def redmine_tracker_by_name(project, name):
        """
        Return a Redmine tracker matching name ('Bugs').
        If there is no match then return the first one!
        """
        all_trackers = project.trackers

        for tracker in all_trackers:
            if tracker.name.lower() == name.lower():
                return tracker

        return all_trackers[0]

    def redmine_priority_by_name(self, name):
        all_priorities = self.rpc.enumeration.filter(resource="issue_priorities")

        for priority in all_priorities:
            if priority.name.lower() == name.lower():
                return priority

        return all_priorities[0]

    def report_issue_from_testexecution(self, execution, user):
        project = self.redmine_project_by_name(execution.run.plan.product.name)
        tracker = self.redmine_tracker_by_name(project, "Bugs")

        # the first Issue Status in Redmine
        status = self.rpc.issue_status.all()[0]

        # try matching TC.priority with IssuePriority in Redmine
        priority = self.redmine_priority_by_name(execution.case.priority.value)

        new_issue = self.rpc.issue.create(
            subject="Failed test: %s" % execution.case.summary,
            description=self._report_comment(execution),
            project_id=project.id,
            tracker_id=tracker.id,
            status_id=status.id,
            priority_id=priority.id,
        )
        new_url = self.bug_system.base_url + "/issues/%d" % new_issue.id

        # and also add a link reference that will be shown in the UI
        LinkReference.objects.get_or_create(
            execution=execution,
            url=new_url,
            is_defect=True,
        )

        return new_url
