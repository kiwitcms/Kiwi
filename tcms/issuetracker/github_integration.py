# -*- coding: utf-8 -*-
"""
    Helper which facilitate actual communications with GitHub.
"""
from tcms.issuetracker.base import IntegrationThread


class GitHubThread(IntegrationThread):
    """
    Execute GitHub RPC code in a thread!

    Executed from the IssueTracker interface methods.
    """

    @staticmethod
    def repo_id(bug_system):
        repo_id = bug_system.base_url.strip().strip("/").lower()
        repo_id = (
            repo_id.replace("https://", "")
            .replace("http://", "")
            .replace("github.com/", "")
        )
        return repo_id

    def __init__(self, rpc, bug_system, execution, bug_id):
        repo_id = self.repo_id(bug_system)
        self.repo = rpc.get_repo(repo_id)

        super().__init__(rpc, bug_system, execution, bug_id)

    def post_comment(self):
        self.repo.get_issue(self.bug_id).create_comment(self.text())
