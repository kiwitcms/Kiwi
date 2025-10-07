# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init


from tcms.rpc.tests.utils import APITestCase
from tcms.xmlrpc_wrapper import XmlRPCFault


class TestAuthLogin(APITestCase):
    """Test Auth.login method"""

    def test_login_with_username(self):
        # assign to a temp variable b/c self.rpc_client a property
        rpc_client = self.rpc_client

        sesson_id = rpc_client.Auth.login(self.api_user.username, "api-testing")
        self.assertIsNotNone(sesson_id)

    def test_login_without_password(self):
        with self.assertRaisesRegex(XmlRPCFault, "Username and password is required"):
            # assign to a temp variable b/c self.rpc_client a property
            rpc_client = self.rpc_client

            rpc_client.Auth.login(self.api_user.username, "")

    def test_login_with_incorrect_password(self):
        with self.assertRaisesRegex(XmlRPCFault, "Wrong username or password"):
            # assign to a temp variable b/c self.rpc_client a property
            rpc_client = self.rpc_client

            rpc_client.Auth.login(self.api_user.username, "kiwi-password")

    def test_login_with_deactivated_account_will_raise_exception(self):
        self.api_user.is_active = False
        self.api_user.save()

        with self.assertRaisesRegex(XmlRPCFault, "Wrong username or password"):
            # assign to a temp variable b/c self.rpc_client a property
            rpc_client = self.rpc_client

            rpc_client.Auth.login(self.api_user.username, "api-testing")


class TestAuthLogout(APITestCase):
    """Test Auth.logout method"""

    def test_logout(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Bug.details"'
        ):
            # assign to a temp variable b/c self.rpc_client a property and calling it twice
            # in sequence results in 1st call logging out and 2nd call logging in automatically
            rpc_client = self.rpc_client

            rpc_client.Auth.logout()
            # this method requires a logged-in user
            rpc_client.Bug.details("http://some.url")
