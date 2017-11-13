# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   Python API for the Nitrate test case management system.
#   Copyright (c) 2012 Red Hat, Inc. All rights reserved.
#   Author: Petr Splichal <psplicha@redhat.com>
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
Python API for the Nitrate test case management system

This module provides a high-level python interface for the nitrate
module. Handles connection to the server automatically, allows to set
custom level of logging and data caching. Supports results coloring.

Synopsis:

    Minimal config file ~/.nitrate::

        [nitrate]
        url = https://nitrate.server/xmlrpc/

    Initialize or create an object::

        testcase = TestCase(1234)
        testrun = TestRun(testplan=<plan>, summary=<summary>)

    Iterate over all container objects::

        for case in TestRun(1234):
            if case.automated:
                case.status = Status("RUNNING")
                case.update()

    Link test case to a test plan::

        testplan.testcases.add(testcase)
        testplan.update()

For details see pydoc documentation for individual modules:

    tcms_api.base ......... Nitrate class, search support
    tcms_api.cache ........ Persistent cache, multicall support
    tcms_api.config ....... Configuration, logging, coloring, caching
    tcms_api.containers ... Container classes implementation
    tcms_api.immutable .... Immutable Nitrate objects
    tcms_api.mutable ...... Mutable Nitrate objects
    tcms_api.teiid ........ Teiid support
    tcms_api.tests ........ Test suite
    tcms_api.utils ........ Utilities
    tcms_api.xmlrpc ....... XMLRPC driver
"""

# Nitrate objects
from tcms_api.base import Nitrate
from tcms_api.immutable import (
    Bug, Build, CaseStatus, Category, Component, PlanStatus, PlanType,
    Priority, Product, RunStatus, Status, Tag, User, Version)
from tcms_api.mutable import (
    Mutable, TestPlan, TestRun, TestCase, CaseRun, CasePlan)
from tcms_api.containers import (
    Container, CaseBugs, CaseComponents, CasePlans, CaseRunBugs, CaseTags,
    ChildPlans, PlanCasePlans, PlanCases, PlanComponents, PlanRuns,
    PlanTags, RunCaseRuns, RunCases, RunTags, TagContainer)

# Various useful utilities
from tcms_api.utils import (
    color, header, human, info, listed, sliced, unlisted)

# Logging, coloring and caching configuration
from tcms_api.config import (
    Config,
    Logging, get_log_level, set_log_level, log,
    LOG_ERROR, LOG_WARN, LOG_INFO, LOG_DEBUG, LOG_CACHE, LOG_DATA, LOG_ALL,

    Coloring, get_color_mode, set_color_mode,
    COLOR_ON, COLOR_OFF, COLOR_AUTO,

    Caching, get_cache_level, set_cache_level,
    CACHE_NONE, CACHE_CHANGES, CACHE_OBJECTS, CACHE_PERSISTENT,
    NEVER_EXPIRE, NEVER_CACHE, MULTICALL_MAX)

# Data communication exceptions
from tcms_api.xmlrpc import NitrateError
from tcms_api.teiid import TeiidError

# Persistent cache and Multicall support
from tcms_api.cache import Cache, multicall_start, multicall_end

__all__ = [
    Nitrate, Mutable, Container,

    Bug, Build, CaseStatus, Category, Component, PlanStatus, PlanType,
    Priority, Product, RunStatus, Status, Tag, User, Version,
    TestPlan, TestRun, TestCase, CaseRun, CasePlan,

    CaseBugs, CaseComponents, CasePlans, CaseRunBugs, CaseTags,
    ChildPlans, PlanCasePlans, PlanCases, PlanComponents, PlanRuns,
    PlanTags, RunCaseRuns, RunCases, RunTags, TagContainer,

    ascii, color, header, human, info, listed, sliced, unlisted,

    Config,
    Logging, get_log_level, set_log_level, log,
    LOG_ERROR, LOG_WARN, LOG_INFO, LOG_DEBUG, LOG_CACHE, LOG_DATA, LOG_ALL,

    Coloring, get_color_mode, set_color_mode,
    COLOR_ON, COLOR_OFF, COLOR_AUTO,

    Caching, get_cache_level, set_cache_level,
    CACHE_NONE, CACHE_CHANGES, CACHE_OBJECTS, CACHE_PERSISTENT,
    NEVER_EXPIRE, NEVER_CACHE, MULTICALL_MAX,

    NitrateError, TeiidError,

    Cache, multicall_start, multicall_end,
]
