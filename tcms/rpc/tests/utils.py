# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

import tcms_api
from django import test

from tcms.tests import PermissionsTestMixin
from tcms.tests.factories import UserFactory
from tcms.utils.permissions import initiate_user_with_default_setups


class APITestCase(test.LiveServerTestCase):
    # preserves data created via migrations
    serialized_rollback = True

    # NOTE: we create the required DB records here because
    # this method is executed *BEFORE* each test scenario!
    @classmethod
    def _fixture_setup(cls):
        # restore the serialized data from initial migrations
        # this includes default groups and permissions
        super()._fixture_setup()

        cls.api_user = UserFactory()
        cls.api_user.set_password("api-testing")
        initiate_user_with_default_setups(cls.api_user)

    @property
    def rpc_client(self):
        return tcms_api.TCMS(
            f"{self.live_server_url}/xml-rpc/",
            self.api_user.username,
            "api-testing",
        ).exec


class APIPermissionsTestCase(PermissionsTestMixin, test.LiveServerTestCase):
    http_method_names = ["api"]
    permission_label = None
    serialized_rollback = True

    # NOTE: see comment in APITestCase._fixture_setup()
    @classmethod
    def _fixture_setup(cls):
        # restore the serialized data from initial migrations
        # this includes default groups and permissions
        super()._fixture_setup()

        cls.check_mandatory_attributes()

        cls.tester = UserFactory()
        cls.tester.set_password("password")
        cls.tester.save()

    @property
    def rpc_client(self):
        return tcms_api.TCMS(
            f"{self.live_server_url}/xml-rpc/",
            self.tester.username,
            "password",
        ).exec

    def verify_api_with_permission(self):
        """
        Call your RPC method under test here and assert the results
        """
        self.fail("Not implemented")

    def verify_api_without_permission(self):
        """
        Call your RPC method under test here and assert the results
        """
        self.fail("Not implemented")
