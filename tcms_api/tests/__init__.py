import unittest
from tcms_api import plugin_helpers


class PluginTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = plugin_helpers.Backend()
