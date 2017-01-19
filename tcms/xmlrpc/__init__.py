# -*- coding: utf-8 -*-
default_app_config = 'tcms.xmlrpc.apps.Config'

"""
The XML-RPC is compatible with Testopia.
Only the arguments are different.

See https://wiki.mozilla.org/Testopia:Documentation:XMLRPC for testopia docs.
"""

from tcms.xmlrpc.filters import autowrap_xmlrpc_apis

__all__ = (
    'auth', 'build', 'testcase', 'testcaserun', 'testcaseplan', 'testopia',
    'testplan', 'testrun', 'user', 'version', 'tag',
)

XMLRPC_VERSION = (1, 1, 0, 'final', 1)


def get_version():
    return XMLRPC_VERSION


autowrap_xmlrpc_apis(__path__, __package__)
