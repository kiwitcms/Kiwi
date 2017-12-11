# -*- coding: utf-8 -*-
__all__ = (
    'auth', 'build', 'testcase', 'testcaserun', 'testcaseplan', 'testopia',
    'testplan', 'testrun', 'user', 'version', 'tag',
)

XMLRPC_VERSION = (1, 1, 0, 'final', 1)


def get_version():
    return XMLRPC_VERSION
