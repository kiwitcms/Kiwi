# -*- coding: utf-8 -*-
import os
import tempfile
from urllib.parse import urlencode

import bugzilla
from bugzilla.exceptions import BugzillaError
from django.conf import settings

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.issuetracker import base
from tcms.xmlrpc_wrapper import XmlRPCFault


class Bugzilla(base.IssueTrackerType):
    """
    Support for Bugzilla. Requires:

    :base_url: For example http://example.com/bugzilla
    :api_url: the XML-RPC URL for your Bugzilla instance.
              For example http://example.com/bugzilla/xmlrpc.cgi
    :api_username: a username registered in Bugzilla
    :api_password: the password for this username

    You can also provide the ``BUGZILLA_AUTH_CACHE_DIR`` setting (in ``product.py``)
    to control where authentication token for Bugzilla will be saved. If this
    is not provided a temporary directory will be used each time we try to login
    into Bugzilla!
    """

    def __init__(self, bug_system, request):
        super().__init__(bug_system, request)

        # directory for Bugzilla credentials
        self._bugzilla_cache_dir = getattr(
            settings, "BUGZILLA_AUTH_CACHE_DIR", tempfile.mkdtemp(prefix=".bugzilla-")
        )

    def _rpc_connection(self):
        if not os.path.exists(self._bugzilla_cache_dir):
            os.makedirs(self._bugzilla_cache_dir, 0o700)

        (api_username, api_password) = self.rpc_credentials

        return bugzilla.Bugzilla(
            self.bug_system.api_url,
            user=api_username,
            password=api_password,
            tokenfile=self._bugzilla_cache_dir + "token",
        )

    def details(self, url):
        try:
            bug = self.rpc.getbug(self.bug_id_from_url(url))

            return {
                "id": bug.id,
                # RHBZ has this attribute while upstream Bugzilla doesn't
                "description": getattr(bug, "description", ""),
                "status": bug.status,
                "title": bug.summary,
                "url": url,
            }
        except (XmlRPCFault, BugzillaError):
            return super().details(url)

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
        return self.rpc.createbug(**buginfo)

    def _report_issue(self, execution, user):
        """
        First attempt *1-click bug report* and if that fails fall back
        to a URL with some of the values pre-defined as query parameters!
        """
        args = {
            "product": execution.build.version.product.name,
            "component": self.get_case_components(execution.case),
            "version": execution.build.version.value,
            "short_desc": f"Test case failure: {execution.case.summary}",
            "comment": self._report_comment(execution, user),
        }

        try:
            new_bug = self.one_click_report(execution, user, args)
            # and also add a link reference that will be shown in the UI
            LinkReference.objects.get_or_create(
                execution=execution,
                url=new_bug.weburl,
                is_defect=True,
            )
            return (new_bug, new_bug.weburl)
        except XmlRPCFault:
            pass

        url = self.bug_system.base_url
        if not url.endswith("/"):
            url += "/"

        return (None, url + "enter_bug.cgi?" + urlencode(args, True))

    def post_comment(self, execution, bug_id):
        self.rpc.update_bugs(
            bug_id, {"comment": {"comment": self.text(execution), "is_private": False}}
        )
