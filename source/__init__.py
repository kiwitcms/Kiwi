# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   This is a Python API for the Nitrate test case management system.
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
High-level API for the Nitrate test case management system.

This module provides a high-level python interface for the nitrate
module. Handles connection to the server automatically, allows to set
custom level of logging and data caching. Supports results coloring.


Config file
~~~~~~~~~~~

To be able to contact the Nitrate server a minimal user configuration
file ~/.nitrate has to be provided in the user home directory:

    [nitrate]
    url = https://nitrate.server/xmlrpc/

Logging
~~~~~~~

Standard log methods from the python 'logging' module are available
under the short name 'log', for example:

    log.debug(message)
    log.info(message)
    log.warn(message)
    log.error(message)

By default, messages of level WARN and up are only displayed. This can
be controlled by setting the current log level. See setLogLevel() for
more details. In addition, you can easily display info messages using:

    info(message)

which prints provided message (to the standard error output) always,
regardless the current log level.


Search support
~~~~~~~~~~~~~~

Multiple Nitrate classes provide the static method 'search' which takes
the search query in the Django QuerySet format which gives an easy
access to the foreign keys and basic search operators. For example:

    Product.search(name="Red Hat Enterprise Linux 6")
    TestPlan.search(name__contains="python")
    TestRun.search(manager__email='login@example.com'):
    TestCase.search(script__startswith='/CoreOS/python')

For the complete list of available operators see Django documentation:
https://docs.djangoproject.com/en/dev/ref/models/querysets/#field-lookups


Test suite
~~~~~~~~~~~

For running the unit test suite additional sections are required in the
configuration file. These contain the url of the test server and the
data of existing objects to be tested, for example:

    [test]
    url = https://test.server/xmlrpc/

    [product]
    id = 60
    name = Red Hat Enterprise Linux 6

    [testplan]
    id = 1234
    name = Test plan
    type = Function
    product = Red Hat Enterprise Linux 6
    version = 6.1
    status = ENABLED

    [testrun]
    id = 6757
    summary = Test Run Summary

    [testcase]
    id = 1234
    summary = Test case summary
    category = Sanity

To exercise the whole test suite just run "python nitrate.py". To test
only subset of tests pick the desired classes on the command line:

    python -m nitrate.api TestCase

"""

from api import *

__all__ = """
        Nitrate Mutable
        Product Version Build
        Category Priority User Bug
        TestPlan PlanType PlanStatus
        TestRun RunStatus
        TestCase CaseStatus
        CaseRun Status

        ascii color listed
        log info setLogLevel
        setCacheLevel CACHE_NONE CACHE_CHANGES CACHE_OBJECTS CACHE_ALL
        setColorMode COLOR_ON COLOR_OFF COLOR_AUTO
        """.split()

