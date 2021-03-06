# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

"""
    This module implements integration with Kiwi TCMS own bug tracking system!
"""

from django.template.loader import render_to_string

from tcms.bugs.models import Bug
from tcms.bugs.views import New
from tcms.core.contrib.linkreference.models import LinkReference
from tcms.issuetracker.base import IssueTrackerType


class KiwiTCMS(IssueTrackerType):
    """
    Support for Kiwi TCMS. Required fields:

    :base_url: the FQDN of the current instance. Used to match against defect URLs.

    The rest of the fields are not used!
    """

    def _rpc_connection(self):
        return None

    def is_adding_testcase_to_issue_disabled(
        self,
    ):  # pylint: disable=invalid-name, no-self-use
        return False

    def details(self, url):
        """
        Provide more details from our own bug tracker!
        """
        bug_id = self.bug_id_from_url(url)
        bug = Bug.objects.filter(pk=bug_id).first()
        if not bug:
            return {}

        result = {
            "title": bug.summary,
            "description": render_to_string(
                "include/bug_details.html", {"object": bug}
            ),
        }

        return result

    def add_testexecution_to_issue(self, executions, issue_url):
        """
        Directly 'link' BUG and TE objects via their m2m
        relationship.

        .. note::

            This method takes extra steps to safeguard from
            bogus input b/c it is called unconditionally from
            API method ``TestCase.add_link()``!
        """
        try:
            bug_id = self.bug_id_from_url(issue_url)
        except AttributeError:
            return

        try:
            bug = Bug.objects.get(pk=bug_id)
        except Bug.DoesNotExist:
            return

        for execution in executions:
            bug.executions.add(execution)

    def report_issue_from_testexecution(self, execution, user):
        """
        Create the new bug using internal API instead of
        going through the RPC layer and return its URL
        """
        data = {
            "reporter": user,
            "summary": "Failed test: %s" % execution.case.summary,
            "product": execution.run.plan.product,
            "version": execution.run.plan.product_version,
            "build": execution.build,
            "text": self._report_comment(execution),
            "_execution": execution,
        }

        bug = New.create_bug(data)

        # link Bug to TE via m2m
        bug.executions.add(execution)

        # and also add a link reference that will be shown in the UI
        LinkReference.objects.get_or_create(
            execution=execution,
            url=bug.get_full_url(),
            is_defect=True,
        )

        return bug.get_full_url()

    @classmethod
    def bug_id_from_url(cls, url):
        """
        Strips the last '/' and returns the PK
        """
        return super().bug_id_from_url(url.strip("/"))
