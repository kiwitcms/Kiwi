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

    def __init__(self, rpc, bug_system, execution, bug_id):
        repo_id = '/'.join(bug_system.base_url.strip().strip('/').split('/')[-2:])
        self.repo = rpc.projects.get(repo_id)

        super().__init__(rpc, bug_system, execution, bug_id)

    def post_comment(self):
        self.repo.issues.get(self.bug_id).notes.create({'body': self.text()})
