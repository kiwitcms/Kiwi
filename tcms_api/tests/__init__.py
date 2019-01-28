import unittest
from tcms_api.plugin_helpers import Backend


class PluginTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = Backend()
