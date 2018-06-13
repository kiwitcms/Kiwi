Python API for the Kiwi TCMS test case management system
========================================================

This package consists of a high-level Python
module (provides natural object interface), a low-level driver
(allows to directly access Kiwi's xmlrpc API) and a command
line interpreter (useful for fast debugging and experimenting).


FEATURES
--------

Among the most essential features are:

    * Natural and concise Python interface
    * Custom level of caching & logging
    * Integrated test suite
    * Utility functions

The main motivation was to hide unnecessary implementation details
wherever possible so that using the API is as concise as possible.

Scripts importing ``tcms_api`` can make use of several useful
helper functions including ``info()`` for printing to stderr, ``listed()``
which converts list into nice human readable form and of course
``log.{debug,info,warn,error}`` for logging.


EXAMPLES
--------

Initialize or create an object::

    testcase = TestCase(1234)
    testrun = TestRun(testplan=<plan>, summary=<summary>)

Default iterators provided for all container objects::

    for case in TestRun(1234):
        if case.automated:
            case.status = TestCaseRunStatus("RUNNING")
            case.update()

Linking case to a plan is as simple as adding an item to a set::

    testplan.testcases.add(testcase)
    testplan.update()

However, it's still possible to use the low-level driver when a
specific features is not implemented yet or not efficient enough::

    case = TCMS()._server.TestCase.filter({'pk': 46490})[0]

For area-specific details see respective module documentation::

    tcms_api.base ......... TCMS class, search support
    tcms_api.config ....... Configuration, logging, caching
    tcms_api.containers ... Container classes implementation
    tcms_api.immutable .... Immutable TCMS objects
    tcms_api.mutable ...... Mutable TCMS objects
    tcms_api.tests ........ Test suite
    tcms_api.utils ........ Utilities
    tcms_api.xmlrpc ....... XMLRPC driver


INSTALLATION
------------

    pip install tcms-api


CONFIGURATION
-------------

To be able to contact the Kiwi TCMS server a minimal user config
file ``~/.tcms.conf`` has to be provided in the user home directory::

    [tcms]
    url = https://kiwi.server/xml-rpc/
    username = myusername
    password = mypassword


AUTHORS
-------

High-level Python module:
Petr Šplíchal, Zbyšek Mráz, Martin Kyral, Lukáš Zachar, Filip
Holec, Aleš Zelinka, Miroslav Vadkerti, Leoš Pol and Iveta
Wiedermann.

Low-level XMLRPC driver:
Airald Hapairai, David Malcolm, Will Woods, Bill Peck, Chenxiong
Qi, Tang Chaobin, Yuguang Wang and Xuqing Kuang.

As of November 2017 this module has been merged with Kiwi TCMS, an
independent fork of the original Nitrate project. The codebase in this
repository is developed independently of the original and may not be
backwards compatible!

COPYRIGHT
---------

Copyright (c) 2012 Red Hat, Inc. All rights reserved.
Copyright (c) 2017 Kiwi TCMS Project and its contributors. All rights reserved.

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.
