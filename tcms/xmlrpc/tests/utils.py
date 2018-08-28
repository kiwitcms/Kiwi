# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

import os
from django import test

import tcms_api
from tcms.tests.factories import UserFactory
from tcms.utils.permissions import initiate_user_with_default_setups


class XmlrpcAPIBaseTest(test.LiveServerTestCase):
    serialized_rollback = True

    # NOTE: we setup the required DB data and API objects here
    # because this method is executed *AFTER* setUpClass() and the
    # serialized rollback is not yet available during setUpClass()
    # execution
    def _fixture_setup(self):
        # restore the serialized data from initial migrations
        # this includes default groups and permissions
        super(XmlrpcAPIBaseTest, self)._fixture_setup()
        self.api_user = UserFactory()
        self.api_user.set_password('api-testing')
        initiate_user_with_default_setups(self.api_user)

        # reset connection to server b/c the address changes for
        # every test and the client caches this as a class attribute
        tcms_api.TCMS._connection = None  # pylint: disable=protected-access

        # WARNING: for now we override the config file
        # until we can pass the testing configuration
        # TODO: change config values instead of overwriting files on disk
        conf_path = os.path.expanduser('~/.tcms.conf')
        conf_fh = open(conf_path, 'w')
        conf_fh.write("""[tcms]
url = %s/xml-rpc/
username = %s
password = %s
""" % (self.live_server_url, self.api_user.username, 'api-testing'))
        conf_fh.close()

        # this is the XML-RPC ServerProxy with cookies support
        self.rpc_client = tcms_api.TCMS()
