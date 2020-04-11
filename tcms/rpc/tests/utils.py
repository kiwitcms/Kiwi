# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

import tcms_api
from django import test

from tcms.tests.factories import UserFactory
from tcms.utils.permissions import initiate_user_with_default_setups


class APITestCase(test.LiveServerTestCase):
    serialized_rollback = True

    # NOTE: we setup the required DB data and API objects here
    # because this method is executed *AFTER* setUpClass() and the
    # serialized rollback is not yet available during setUpClass()
    # execution
    def _fixture_setup(self):
        # restore the serialized data from initial migrations
        # this includes default groups and permissions
        super()._fixture_setup()
        self.api_user = UserFactory()
        self.api_user.set_password('api-testing')
        initiate_user_with_default_setups(self.api_user)

        # this is the XML-RPC ServerProxy with cookies support
        self.rpc_client = tcms_api.xmlrpc.TCMSXmlrpc(
            self.api_user.username,
            'api-testing',
            '%s/xml-rpc/' % self.live_server_url,
        ).server
