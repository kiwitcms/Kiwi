# -*- coding: utf-8 -*-
"""
    Helper which facilitates actual communications with GitLab.
"""
from tcms.issuetracker.base import IntegrationThread


class GitlabThread(IntegrationThread):
    """
    Execute Gitlab RPC code in a thread!

    Executed from the IssueTracker interface methods.
    """

    @staticmethod
    def repo_id(bug_system):
        return "/".join(bug_system.base_url.strip().strip("/").split("/")[-2:])

    def __init__(self, rpc, bug_system, execution, bug_id):
        repo_id = self.repo_id(bug_system)
        self.repo = rpc.projects.get(repo_id)

        super().__init__(rpc, bug_system, execution, bug_id)

    def post_comment(self):
        self.repo.issues.get(self.bug_id).notes.create({"body": self.text()})
