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
This module provides a dictionary based Python interface for the
Kiwi TCMS test case management system.

Installation::

    pip install tcms-api

Minimal config file ``~/.tcms.conf``::

    [tcms]
    url = https://tcms.server/xml-rpc/
    username = your-username
    password = your-password

For Kerberos specify ``use_mod_kerb = True`` key!
It's also possible to provide system-wide config in ``/etc/tcms.conf``.

Connect to backend::

    from tcms_api import TCMS

    rpc_client = TCMS()

    for test_case in rpc_client.exec.TestCase.filter({'pk': 46490}):
        print(test_case)

"""
import os
from configparser import ConfigParser

from .xmlrpc import TCMSXmlrpc, TCMSKerbXmlrpc


class TCMS:  # pylint: disable=too-few-public-methods
    """
    Takes care of initiating the connection to the TCMS server and
    parses user configuration.
    """

    _connection = None
    _path = os.path.expanduser("~/.tcms.conf")

    def __init__(self):
        # Connect to the server unless already connected
        if TCMS._connection is not None:
            return

        # Try system settings when the config does not exist in user directory
        if not os.path.exists(self._path):
            self._path = "/etc/tcms.conf"
        if not os.path.exists(self._path):
            raise Exception("Config file '%s' not found" % self._path)

        config = ConfigParser()
        config.read(self._path)

        # Make sure the server URL is set
        try:
            config['tcms']['url'] is not None
        except (KeyError, AttributeError):
            raise Exception("No url found in %s" % self._path)
        self._parsed = True

        if config['tcms'].get('use_mod_kerb', False):
            # use Kerberos
            TCMS._connection = TCMSKerbXmlrpc(config['tcms']['url']).server

        # use plain authentication otherwise
        try:
            TCMS._connection = TCMSXmlrpc(config['tcms']['username'],
                                          config['tcms']['password'],
                                          config['tcms']['url']).server
        except KeyError:
            raise Exception("username/password are required in %s" % self._path)

    @property
    def exec(self):
        """
        Property that returns the underlying XML-RPC connection on which
        you can call various server-side functions.
        """
        return TCMS._connection
