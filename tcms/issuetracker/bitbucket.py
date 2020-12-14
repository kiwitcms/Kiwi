# -*- coding: utf-8 -*-
import requests
from requests.auth import HTTPBasicAuth

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.issuetracker.base import IntegrationThread, IssueTrackerType


class BitBucketAPI:
    """
    BitBucket API interaction class.

    """

    def __init__(self, base_url=None, api_username=None, api_password=None):
        api_version = "2.0"
        self.endpoint_url = self._construct_endpoint_url(api_version, base_url)
        self.headers = {
            "Accept": "application/json",
            "Content-type": "application/json",
        }
        self.auth = HTTPBasicAuth(api_username, api_password)

    def create_issue(self, data):
        url = "{0}{1}".format(self.endpoint_url, "/issues")
        return self._request(
            "POST", url, headers=self.headers, auth=self.auth, json=data
        )

    def get_issue(self, issue_id):
        url = "{0}{1}{2}".format(self.endpoint_url, "/issues/", issue_id)
        return self._request("GET", url, headers=self.headers, auth=self.auth)

    def update_issue(self, issue_id, data):
        url = "{0}{1}{2}{3}".format(self.endpoint_url, "/issues/", issue_id, "/changes")
        return self._request(
            "POST", url, headers=self.headers, auth=self.auth, json=data
        )

    def add_comment(self, issue_id, comment):
        url = "{0}{1}{2}{3}".format(
            self.endpoint_url, "/issues/", issue_id, "/comments/"
        )
        return self._request(
            "POST", url, headers=self.headers, auth=self.auth, json=comment
        )

    def get_comments(self, issue_id):
        url = "{0}{1}{2}{3}".format(
            self.endpoint_url, "/issues/", issue_id, "/comments?sort=-updated_on"
        )
        return self._request("GET", url, headers=self.headers, auth=self.auth)

    def delete_comment(self, issue_id, comment_id):
        url = "{0}{1}{2}{3}{4}".format(
            self.endpoint_url, "/issues/", issue_id, "/comments/", comment_id
        )
        return self._request("DELETE", url, headers=self.headers, auth=self.auth)

    @staticmethod
    def _request(method, url, **kwargs):
        if method == "DELETE":
            return requests.request(method, url, **kwargs)
        return requests.request(method, url, **kwargs).json()

    @staticmethod
    def _construct_endpoint_url(api_version, url):
        splitted_url = url.replace("https://", "").split("/")
        base_url = "https://api.bitbucket.org"
        workspace = splitted_url[1]
        repository = splitted_url[2]
        endpoint_url = "{0}/{1}/{2}/{3}/{4}".format(
            base_url, api_version, "repositories", workspace, repository
        )
        return endpoint_url


class BitBucketThread(IntegrationThread):
    """
    Execute BitBucket code in a thread!

    Executed from the IssueTracker interface methods.
    """

    def post_comment(self):
        comment_body = {"content": {"raw": self.text().replace("\n", "\n\n")}}
        self.rpc.add_comment(self.bug_id, comment_body)


class BitBucket(IssueTrackerType):
    """
    Support for BitBucket. Requires:

    :base_url: Repository URL - e.g. https://bitbucket.org/{workspace}/{repository}
    :api_username: BitBucket Username
    :api_password: BitBucket App Password - needs Issues: Read & write permission.

    .. note::

        You can leave the ``api_url`` field blank because the integration
        code doesn't use it!

    .. warning::

        ``api_username`` is your BitBucket username, which you use to log in.

    .. note::

        ``api_password`` is "App Password" created in BitBucket.
        Here is a guide about creating and using an "App Password";
        https://support.atlassian.com/bitbucket-cloud/docs/app-passwords/
    """

    it_class = BitBucketThread

    def _rpc_connection(self):
        return BitBucketAPI(
            self.bug_system.base_url,
            api_username=self.bug_system.api_username,
            api_password=self.bug_system.api_password,
        )

    def is_adding_testcase_to_issue_disabled(self):
        return not (
            self.bug_system.base_url
            and self.bug_system.api_username
            and self.bug_system.api_password
        )

    def report_issue_from_testexecution(self, execution, user):
        """
        BitBucket creates the Issue with Title and Description
        """

        data = {
            "title": "Failed test: %s" % execution.case.summary,
            "kind": "bug",
            "priority": "major",
            "content": {"raw": self._report_comment(execution).replace("\n", "\r\n")},
        }

        try:
            issue = self.rpc.create_issue(data)

            issue_url = self.bug_system.base_url + "/issues/" + str(issue["id"])
            # add a link reference that will be shown in the UI
            LinkReference.objects.get_or_create(
                execution=execution,
                url=issue_url,
                is_defect=True,
            )

            return issue_url
        except Exception:  # pylint: disable=broad-except
            # something above didn't work so return a link for manually
            # entering issue details with info pre-filled
            url = self.bug_system.base_url
            if not url.endswith("/"):
                url += "/"

            return url + "issues/new"

    def details(self, url):
        """
        Return issue details from BitBucket
        """
        issue = self.rpc.get_issue(self.bug_id_from_url(url))
        return {
            "title": issue["title"],
            "description": issue["content"]["raw"],
        }
