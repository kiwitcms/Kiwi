# -*- coding: utf-8 -*-

"""
The XML-RPC is compatible with Testopia.
Only the arguments are different.

See https://wiki.mozilla.org/Testopia:Documentation:XMLRPC for testopia docs.
"""

__all__ = (
    'auth', 'build', 'testcase', 'testcaserun', 'testcaseplan', 'testopia',
    'testplan', 'testrun', 'user', 'version', 'tag',
)

XMLRPC_VERSION = (1, 1, 0, 'final', 1)


def get_version():
    return XMLRPC_VERSION
