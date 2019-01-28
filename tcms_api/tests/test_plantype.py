from unittest.mock import MagicMock

from . import PluginTestCase


class GivenPlanTypeExistsInDatabase(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.PlanType.filter = MagicMock(return_value=[{'id': 4}])
        cls.backend.rpc.PlanType.create = MagicMock(return_value={'id': 5})

    def test_when_get_plan_type_id_then_will_reuse_it(self):
        pt_id = self.backend.get_plan_type_id()
        self.assertEqual(pt_id, 4)
        self.backend.rpc.PlanType.create.assert_not_called()


class GivenPlanTypeDoesntExistInDatabase(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.PlanType.filter = MagicMock(return_value=[])
        cls.backend.rpc.PlanType.create = MagicMock(return_value={'id': 5})

    def test_when_get_plan_type_id_then_will_add_it(self):
        pt_id = self.backend.get_plan_type_id()
        self.assertEqual(pt_id, 5)
        self.backend.rpc.PlanType.create.assert_called_with({
            'name': 'Integration'})
