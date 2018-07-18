# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   Python API for the Kiwi TCMS test case management system.
#   Copyright (c) 2012 Red Hat, Inc. All rights reserved.
#   Author: Petr Splichal <psplicha@redhat.com>
#
#   Copyright (c) 2018 Kiwi TCMS project. All rights reserved.
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
To be able to contact the TCMS server a minimal user configuration
file ~/.tcms.conf has to be provided in the user home directory:

    [tcms]
    url = https://tcms.server/xml-rpc/
    username = login
    password = secret

It's also possible to provide system-wide config in /etc/tcms.conf.
"""
import os
from configparser import ConfigParser


class Section(object):
    """ Trivial class for sections """
    pass


class Config(object):
    """ User configuration """

    _parsed = False
    # Config path
    path = os.path.expanduser("~/.tcms.conf")

    def __init__(self):
        """ Initialize the configuration """
        # Nothing to do if already parsed
        if self._parsed:
            return

        # Try system settings when the config does not exist in user directory
        if not os.path.exists(self.path):
            self.path = "/etc/tcms.conf"
        if not os.path.exists(self.path):
            raise Exception("Config file '%s' not found" % self.path)

        # Parse the config
        try:
            parser = ConfigParser()
            parser.read([self.path])
            for section in parser.sections():
                # Create a new section object for each section
                setattr(self, section, Section())
                # Set its attributes to section contents (adjust types)
                for name, value in parser.items(section):
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                    if value == "True":
                        value = True
                    if value == "False":
                        value = False
                    setattr(getattr(self, section), name, value)
        except ConfigParser.Error:
            raise Exception("Cannot read the config file")

        # Make sure the server URL is set
        try:
            self.tcms.url is not None
        except AttributeError:
            raise Exception("No url found in the config file")
        self._parsed = True
