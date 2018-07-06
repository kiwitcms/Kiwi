# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   Python API for the Kiwi TCMS test case management system.
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
Kiwi TCMS class and internal utilities

Search support
~~~~~~~~~~~~~~

Multiple Kiwi TCMS classes provide the static method 'search' which takes
the search query in the Django QuerySet format which gives an easy
access to the foreign keys and basic search operators. For example:

    Product.search(name="Red Hat Enterprise Linux 6")
    TestPlan.search(name__contains="python")
    TestRun.search(manager__email='login@example.com'):
    TestCase.search(script__startswith='/CoreOS/python')

For the complete list of available operators see Django documentation:
https://docs.djangoproject.com/en/dev/ref/models/querysets/#field-lookups
"""

import tcms_api.xmlrpc as xmlrpc

from tcms_api.config import log, Config


class TCMS(object):
    """
    General TCMS Object.

    Takes care of initiating the connection to the TCMS server and
    parses user configuration.
    """

    _connection = None

    @property
    def _server(self):
        """ Connection to the server """

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

        # Return existing connection
        return TCMS._connection
