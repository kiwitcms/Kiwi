# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

from xmlrpc.client import Fault as XmlRPCFault

from tcms.rpc.tests.utils import APITestCase


class TestAuthLogin(APITestCase):
    """Test Auth.login method"""

    def _fixture_setup(self):
        super()._fixture_setup()

        self.rpc_client.Auth.logout()

    def test_login_with_username(self):
        sesson_id = self.rpc_client.Auth.login(self.api_user.username, "api-testing")
        self.assertIsNotNone(sesson_id)

    def test_login_without_password(self):
        with self.assertRaisesRegex(XmlRPCFault, "Username and password is required"):
            self.rpc_client.Auth.login(self.api_user.username, "")

    def test_login_with_incorrect_password(self):
        with self.assertRaisesRegex(XmlRPCFault, "Wrong username or password"):
            self.rpc_client.Auth.login(self.api_user.username, "kiwi-password")


class TestAuthLogout(APITestCase):
    """Test Auth.logout method"""

    def test_logout(self):
        self.rpc_client.Auth.logout()
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Bug.details"'
        ):
            # this method requires a logged-in user
            self.rpc_client.Bug.details("http://some.url")
