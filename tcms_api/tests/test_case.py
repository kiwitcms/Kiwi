from unittest.mock import MagicMock

from . import PluginTestCase


class GivenTestCaseExistsInDatabase(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.TestCase.filter = MagicMock(
            return_value=[{'case_id': 34}])
        cls.backend.rpc.TestCase.create = MagicMock()

    def test_when_test_case_get_or_create_then_reuses_it(self):
        test_case = self.backend.test_case_get_or_create('Automated test case')
        self.assertEqual(test_case['case_id'], 34)
        self.backend.rpc.TestCase.create.assert_not_called()


class GivenTestCaseDoesNotExistInDatabase(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.TestCase.filter = MagicMock(return_value=[])
        cls.backend.rpc.TestCase.create = MagicMock(
            return_value={'case_id': 43})
        cls.backend.category_id = 999
        cls.backend.product_id = 888
        cls.backend.priority_id = 777
        cls.backend.confirmed_id = 666

    def test_when_test_case_get_or_create_then_creates_it(self):
        test_case = self.backend.test_case_get_or_create('Automated test case')
        self.assertEqual(test_case['case_id'], 43)
        self.backend.rpc.TestCase.create.assert_called_with({
            'summary': 'Automated test case',
            'category': 999,
            'product': 888,
            'priority': 777,
            'case_status': 666,
            'notes': 'Created by tcms_api.plugin_helpers.Backend',
        })
