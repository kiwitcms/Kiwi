# pylint: disable=invalid-name
import os
from unittest.mock import MagicMock, patch

from . import PluginTestCase


class Given_TCMS_PRODUCT_IsPresent(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.TestPlan.filter = MagicMock(return_value=[])
        cls.backend.rpc.Product.filter = MagicMock(return_value=[{'id': 44}])

    def test_when_adding_product_then_will_use_it(self):
        with patch.dict(os.environ, {
                'TCMS_PRODUCT': 'p.Test',
                'TRAVIS_REPO_SLUG': 'kiwitcms/tap.backend',
                'JOB_NAME': 'TAP Plugin',
        }, True):
            product_id, product_name = self.backend.get_product_id(0)
            self.assertEqual(product_id, 44)
            self.assertEqual(product_name, 'p.Test')


class Given_TRAVIS_REPO_SLUG_IsPresent(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.TestPlan.filter = MagicMock(return_value=[])
        cls.backend.rpc.Product.filter = MagicMock(return_value=[{'id': 44}])

    def test_when_adding_product_then_will_use_it(self):
        with patch.dict(os.environ, {
                'TRAVIS_REPO_SLUG': 'kiwitcms/tap.backend',
                'JOB_NAME': 'TAP Plugin',
        }, True):
            product_id, product_name = self.backend.get_product_id(0)
            self.assertEqual(product_id, 44)
            self.assertEqual(product_name, 'kiwitcms/tap.backend')


class Given_JOB_NAME_IsPresent(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.TestPlan.filter = MagicMock(return_value=[])
        cls.backend.rpc.Product.filter = MagicMock(return_value=[{'id': 44}])

    def test_when_adding_product_then_will_use_it(self):
        with patch.dict(os.environ, {
                'JOB_NAME': 'TAP Plugin',
        }, True):
            product_id, product_name = self.backend.get_product_id(0)
            self.assertEqual(product_id, 44)
            self.assertEqual(product_name, 'TAP Plugin')


class GivenProductEnvironmentIsNotPresent(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.TestPlan.filter = MagicMock(return_value=[])

    def test_when_adding_product_then_will_raise(self):
        with patch.dict(os.environ, {}, True):
            with self.assertRaisesRegex(Exception,
                                        'Product name not defined'):
                self.backend.get_product_id(0)


class GivenTestPlanExistsInDatabase(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.TestPlan.filter = MagicMock(return_value=[{
            'product_id': 44,
            'product': 'Four-forty',
        }])
        cls.backend.rpc.Product.filter = MagicMock()

    def test_when_get_product_id_then_use_product_from_plan(self):
        product_id, product_name = self.backend.get_product_id(0)
        self.assertEqual(product_id, 44)
        self.assertEqual(product_name, 'Four-forty')
        self.backend.rpc.Product.filter.assert_not_called()


class GivenProductExistsInDatabase(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.TestPlan.filter = MagicMock(return_value=[])
        cls.backend.rpc.Product.filter = MagicMock(return_value=[{'id': 44}])
        cls.backend.rpc.Product.create = MagicMock()

    def test_when_adding_product_then_will_reuse_it(self):
        with patch.dict(os.environ, {
                'TCMS_PRODUCT': 'p.Test',
        }, True):
            product_id, product_name = self.backend.get_product_id(0)
            self.assertEqual(product_id, 44)
            self.assertEqual(product_name, 'p.Test')
            self.backend.rpc.Product.create.assert_not_called()


class GivenProductDoesntExistInDatabase(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.TestPlan.filter = MagicMock(return_value=[])
        cls.backend.rpc.Product.filter = MagicMock(return_value=[])
        cls.backend.rpc.Classification.filter = MagicMock(
            return_value=[{'id': 4}])
        cls.backend.rpc.Product.create = MagicMock(return_value={'id': 55})

    def test_when_adding_product_then_will_add_it(self):
        with patch.dict(os.environ, {
                'TCMS_PRODUCT': 'p.Test',
        }, True):
            product_id, product_name = self.backend.get_product_id(0)
            self.assertEqual(product_id, 55)
            self.assertEqual(product_name, 'p.Test')
            self.backend.rpc.Product.create.assert_called_with({
                'name': 'p.Test',
                'classification_id': 4,
            })
