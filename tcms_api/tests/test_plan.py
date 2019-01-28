# pylint: disable=invalid-name
from unittest.mock import MagicMock

from . import PluginTestCase


class GivenRunExistsInDatabase(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.TestRun.filter = MagicMock(
            return_value=[{'plan_id': 4}])
        cls.backend.rpc.TestPlan.filter = MagicMock()
        cls.backend.rpc.TestPlan.create = MagicMock()

    def test_when_get_plan_id_then_will_reuse_TestPlan(self):
        plan_id = self.backend.get_plan_id(0)
        self.assertEqual(plan_id, 4)
        self.backend.rpc.TestPlan.filter.assert_not_called()
        self.backend.rpc.TestPlan.create.assert_not_called()


class GivenRunDoesntExistInDatabase(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.TestRun.filter = MagicMock(return_value=[])
        cls.backend.get_product_id = MagicMock(return_value=(4, 'p.Four'))
        cls.backend.get_version_id = MagicMock(return_value=(44, 'v.Test'))
        cls.backend.get_plan_type_id = MagicMock(return_value=10)

    def test_when_get_plan_id_with_existing_TestPlan_then_will_reuse_it(self):
        self.backend.rpc.TestPlan.filter = MagicMock(
            return_value=[{'plan_id': 400}])
        self.backend.rpc.TestPlan.create = MagicMock()

        plan_id = self.backend.get_plan_id(0)
        self.assertEqual(plan_id, 400)
        self.backend.rpc.TestPlan.create.assert_not_called()

    def test_when_get_plan_id_with_non_existing_TP_then_will_create_it(self):
        self.backend.rpc.TestPlan.filter = MagicMock(return_value=[])
        self.backend.rpc.TestPlan.create = MagicMock(
            return_value={'plan_id': 500})

        plan_id = self.backend.get_plan_id(0)
        self.assertEqual(plan_id, 500)
        self.backend.rpc.TestPlan.create.assert_called_with({
            'name': '[TAP] Plan for p.Four (v.Test)',
            'text': 'Created by tcms_api.plugin_helpers.Backend',
            'product': 4,
            'product_version': 44,
            'is_active': True,
            'type': 10,
        })


class GivenEmptyTestPlan(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.TestCase.filter = MagicMock(return_value=[])
        cls.backend.rpc.TestPlan.add_case = MagicMock()

    def test_when_add_test_case_to_plan_then_TestCase_is_added(self):
        self.backend.add_test_case_to_plan(11, 22)
        self.backend.rpc.TestPlan.add_case.assert_called_with(22, 11)


class GivenTestPlanWithTestCases(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.TestCase.filter = MagicMock(return_value=[{}])
        cls.backend.rpc.TestPlan.add_case = MagicMock()

    def test_when_add_test_case_to_plan_then_TestCase_is_not_added(self):
        self.backend.add_test_case_to_plan(11, 22)
        self.backend.rpc.TestPlan.add_case.assert_not_called()
