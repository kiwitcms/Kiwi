# -*- coding: utf-8 -*-
import os
import tempfile
from urllib.parse import urlencode
from xmlrpc.client import Fault

import bugzilla
from django.conf import settings

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.issuetracker import base


class BugzillaThread(base.IntegrationThread):
    """
    Execute Bugzilla RPC code in a thread!

    Executed from the IssueTracker interface methods.
    """

    def post_comment(self):
        self.rpc.update_bugs(
            self.bug_id, {"comment": {"comment": self.text(), "is_private": False}}
        )


class Bugzilla(base.IssueTrackerType):
    """
    Support for Bugzilla. Requires:

    :base_url: - e.g. http://example.com/bugzilla
    :api_url: - the XML-RPC URL for your Bugzilla instance
    :api_username: - a username registered in Bugzilla
    :api_password: - the password for this username

    You can also provide the ``BUGZILLA_AUTH_CACHE_DIR`` setting (in ``product.py``)
    to control where authentication cookies for Bugzilla will be saved. If this
    is not provided a temporary directory will be used each time we try to login
    into Bugzilla!
    """

    it_class = BugzillaThread

    def __init__(self, bug_system, request):
        super().__init__(bug_system, request)

        # directory for Bugzilla credentials
        self._bugzilla_cache_dir = getattr(
            settings, "BUGZILLA_AUTH_CACHE_DIR", tempfile.mkdtemp(prefix=".bugzilla-")
        )

    def _rpc_connection(self):
        if not os.path.exists(self._bugzilla_cache_dir):
            os.makedirs(self._bugzilla_cache_dir, 0o700)

        return bugzilla.Bugzilla(
            self.bug_system.api_url,
            user=self.bug_system.api_username,
            password=self.bug_system.api_password,
            cookiefile=self._bugzilla_cache_dir + "cookie",
            tokenfile=self._bugzilla_cache_dir + "token",
        )

    def one_click_report(
        self, execution, user, args
    ):  # pylint: disable=unused-argument
        """
        Attempt 1-click bug report! Unmodified Bugzilla requires
        *Product*, *Component*, *Version* and *Summary*!
        *OS* and *Hardware* fields are set to *All*!

        .. warning::

            This can fail due to Bugzilla requiring more fields,
            because the API user doesn't have permissions to report in
            the chosen Product, becase TC info is incomplete or because
            any of the specified fields doesn't exist!

            It is up to the Bugzilla/TCMS admin to make sure these are
            in sync! Alternatively inherit this class and override this
            method!
        """
        buginfo = args.copy()
        buginfo["op_sys"] = "All"
        buginfo["rep_platform"] = "All"
        return self.rpc.createbug(**buginfo).weburl

    def report_issue_from_testexecution(self, execution, user):
        """
        First attempt *1-click bug report* and if that fails fall back
        to a URL with some of the values pre-defined as query parameters!
        """
        args = {}
        args["product"] = execution.run.plan.product.name
        args["component"] = self.get_case_components(execution.case)
        args["version"] = execution.run.plan.product_version.value

        args["short_desc"] = "Test case failure: %s" % execution.case.summary
        args["comment"] = self._report_comment(execution)

        try:
            new_bug_url = self.one_click_report(execution, user, args)
            # and also add a link reference that will be shown in the UI
            LinkReference.objects.get_or_create(
                execution=execution,
                url=new_bug_url,
                is_defect=True,
            )
            return new_bug_url
        except Fault:
            pass

        url = self.bug_system.base_url
        if not url.endswith("/"):
            url += "/"

        return url + "enter_bug.cgi?" + urlencode(args, True)
