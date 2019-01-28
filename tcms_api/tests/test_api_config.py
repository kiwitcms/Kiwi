# pylint: disable=invalid-name
import unittest


class GivenConfigurationFileExists(unittest.TestCase):
    @unittest.skip('not implemented')
    def test_when_backend_initializes_then_uses_config(self):
        pass


class GivenConfigurationFileDoesntExist(unittest.TestCase):
    @unittest.skip('not implemented')
    def test_when_backend_initializes_then_uses_environment(self):
        pass

    @unittest.skip('not implemented')
    def test_when_TCMS_API_URL_is_not_configured_then_fails(self):
        pass

    @unittest.skip('not implemented')
    def test_when_TCMS_USERNAME_is_not_configured_then_fails(self):
        pass

    @unittest.skip('not implemented')
    def test_when_TCMS_PASSWORD_is_not_configured_then_fails(self):
        pass
