# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   Python API for the Kiwi TCMS test case management system.
#   Copyright (c) 2012 Red Hat, Inc. All rights reserved.
#   Author: Petr Splichal <psplicha@redhat.com>
#
#   Copyright (c) 2018 Kiwi TCMS project. All rights reserved.
#   Author: Alexander Todorov <info@kiwitcms.org>
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   This library is free software; you can redistribute it and/or
#   modify it under the terms of the GNU Lesser General Public
#   License as published by the Free Software Foundation; either
#   version 2.1 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
Python API for the Kiwi TCMS test case management system

This module provides a high-level python interface.
Handles connection to the server automatically, allows to set
custom level of logging and data caching.

Synopsis:

    Minimal config file ~/.tcms.conf::

        [tcms]
        url = https://tcms.server/xml-rpc/

    Initialize or create an object::

        testcase = TestCase(1234)
        testrun = TestRun(testplan=<plan>, summary=<summary>)

    Iterate over all container objects::

        for case in TestRun(1234):
            if case.automated:
                case.status = TestCaseRunStatus("RUNNING")
                case.update()

    Link test case to a test plan::

        testplan.testcases.add(testcase)
        testplan.update()

For details see pydoc documentation for individual modules:

    tcms_api.base ......... TCMS class, search support
    tcms_api.config ....... Configuration, logging, caching
    tcms_api.containers ... Container classes implementation
    tcms_api.immutable .... Immutable TCMS objects
    tcms_api.mutable ...... Mutable TCMS objects
    tcms_api.tests ........ Test suite
    tcms_api.utils ........ Utilities
    tcms_api.xmlrpc ....... XMLRPC driver
"""

# TCMS objects
from tcms_api.base import TCMS
from tcms_api.immutable import (
    Bug, Build, CaseStatus, Category, Component, PlanType,
    Priority, Product, TestCaseRunStatus, Tag, User, Version)
from tcms_api.mutable import (
    Mutable, TestPlan, TestRun, TestCase, TestCaseRun)
from tcms_api.containers import (
    Container, CaseBugs, CaseComponents, CaseRunBugs, CaseTags,
    ChildPlans, PlanCases, PlanRuns,
    PlanTags, RunCaseRuns, RunCases, RunTags, TagContainer)

# Various useful utilities
from tcms_api.utils import header, human, info, listed, unlisted

# Logging and caching configuration
from tcms_api.config import (
    Config,
    Logging, get_log_level, set_log_level, log,
    LOG_ERROR, LOG_WARN, LOG_INFO, LOG_DEBUG, LOG_CACHE, LOG_DATA, LOG_ALL,

    Caching, get_cache_level, set_cache_level,
    CACHE_NONE, CACHE_OBJECTS, NEVER_CACHE, NEVER_EXPIRE)

# Data communication exceptions
from tcms_api.xmlrpc import TCMSError

__all__ = [
    'TCMS', 'Mutable', 'Container',

    'Bug', 'Build', 'CaseStatus', 'Category', 'Component', 'PlanType',
    'Priority', 'Product', 'TestCaseRunStatus', 'Tag', 'User', 'Version',
    'TestPlan', 'TestRun', 'TestCase', 'TestCaseRun',

    'CaseBugs', 'CaseComponents', 'CaseRunBugs', 'CaseTags',
    'ChildPlans', 'PlanCases', 'PlanRuns',
    'PlanTags', 'RunCaseRuns', 'RunCases', 'RunTags', 'TagContainer',

    'header', 'human', 'info', 'listed', 'unlisted',

    'Config',
    'Logging', 'get_log_level', 'set_log_level', 'log',
    'LOG_ERROR', 'LOG_WARN', 'LOG_INFO', 'LOG_DEBUG', 'LOG_CACHE', 'LOG_DATA', 'LOG_ALL',

    'Caching', 'get_cache_level', 'set_cache_level',
    'CACHE_NONE', 'CACHE_OBJECTS',
    'NEVER_EXPIRE', 'NEVER_CACHE',

    'TCMSError',
]
