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

This module provides a low-level(dictionary based) Python interface.

Synopsis:

    Minimal config file ~/.tcms.conf::

        [tcms]
        url = https://tcms.server/xml-rpc/
        username = your-username
        password = your-password


    Connect to backend::

        from tcms_api import TCMS

        rpc_client = TCMS()

        for test_case in rpc_client.exec.TestCase.filter({'pk': 46490}):
            print(test_case)
"""
import tcms_api.xmlrpc as xmlrpc
from tcms_api.config import (
    Config,
    Logging, get_log_level, set_log_level, log,
    LOG_ERROR, LOG_WARN, LOG_INFO, LOG_DEBUG, LOG_CACHE, LOG_DATA, LOG_ALL)  # flake8: noqa


class TCMS(object):
    """
    Takes care of initiating the connection to the TCMS server and
    parses user configuration.
    """

    _connection = None

    def __init__(self):
        # Connect to the server unless already connected
        if TCMS._connection is None:
            log.debug("Contacting server {0}".format(Config().tcms.url))
            if hasattr(Config().tcms, 'use_mod_kerb') and Config().tcms.use_mod_kerb:
                # use Kerberos
                TCMS._connection = xmlrpc.TCMSKerbXmlrpc(
                    Config().tcms.url).server
            else:
                # use plain authentication otherwise
                TCMS._connection = xmlrpc.TCMSXmlrpc(
                    Config().tcms.username,
                    Config().tcms.password,
                    Config().tcms.url).server

    @property
    def exec(self):
        """
        Property that returns the underlying XML-RPC connection on which
        you can call various server-side functions.
        """
        return TCMS._connection
