# pylint: disable=invalid-name

import os
from unittest.mock import MagicMock, patch

from . import PluginTestCase


class Given_TCMS_PRODUCT_VERSION_IsPresent(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.Version.filter = MagicMock(return_value=[{'id': 4}])

    def test_when_get_version_id_then_will_use_it(self):
        with patch.dict(os.environ, {
                'TCMS_PRODUCT_VERSION': 'v.Test',
                'TRAVIS_COMMIT': 'commit-d86f418',
                'TRAVIS_PULL_REQUEST_SHA': 'pr-sha-426a95d',
                'GIT_COMMIT': 'git-d4c2683',
        }, True):
            version_id, version_val = self.backend.get_version_id(0)
            self.assertEqual(version_id, 4)
            self.assertEqual(version_val, 'v.Test')


class Given_TRAVIS_COMMIT_IsPresent(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.Version.filter = MagicMock(return_value=[{'id': 4}])

    def test_when_get_version_id_then_will_use_it(self):
        with patch.dict(os.environ, {
                'TRAVIS_COMMIT': 'commit-d86f418',
                'TRAVIS_PULL_REQUEST_SHA': 'pr-sha-426a95d',
                'GIT_COMMIT': 'git-d4c2683',
        }, True):
            version_id, version_val = self.backend.get_version_id(0)
            self.assertEqual(version_id, 4)
            self.assertEqual(version_val, 'commit-d86f418')


class Given_TRAVIS_PULL_REQUEST_SHA_IsPresent(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.Version.filter = MagicMock(return_value=[{'id': 4}])

    def test_when_get_version_id_then_will_use_it(self):
        with patch.dict(os.environ, {
                'TRAVIS_PULL_REQUEST_SHA': 'pr-sha-426a95d',
                'GIT_COMMIT': 'git-d4c2683',
        }, True):
            version_id, version_val = self.backend.get_version_id(0)
            self.assertEqual(version_id, 4)
            self.assertEqual(version_val, 'pr-sha-426a95d')


class Given_GIT_COMMIT_IsPresent(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.Version.filter = MagicMock(return_value=[{'id': 4}])

    def test_when_get_version_id_then_will_use_it(self):
        with patch.dict(os.environ, {
                'GIT_COMMIT': 'git-d4c2683',
        }, True):
            version_id, version_val = self.backend.get_version_id(0)
            self.assertEqual(version_id, 4)
            self.assertEqual(version_val, 'git-d4c2683')


class GivenVersionEnvironmentIsNotPresent(PluginTestCase):
    def test_when_get_version_id_then_will_raise(self):
        with patch.dict(os.environ, {}, True):
            with self.assertRaisesRegex(Exception,
                                        'Version value not defined'):
                self.backend.get_version_id(0)


class GivenVersionExistsInDatabase(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.Version.filter = MagicMock(return_value=[{'id': 4}])
        cls.backend.rpc.Version.create = MagicMock(return_value={'id': 5})

    def test_when_get_version_id_then_will_reuse_it(self):
        with patch.dict(os.environ, {
                'TCMS_PRODUCT_VERSION': 'v.Test',
        }, True):
            version_id, version_val = self.backend.get_version_id(0)
            self.assertEqual(version_id, 4)
            self.assertEqual(version_val, 'v.Test')
            self.backend.rpc.Version.create.assert_not_called()


class GivenVersionDoesntExistInDatabase(PluginTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.rpc = MagicMock()
        cls.backend.rpc.Version.filter = MagicMock(return_value=[])
        cls.backend.rpc.Version.create = MagicMock(return_value={'id': 5})

    def test_when_get_version_id_then_will_add_it(self):
        with patch.dict(os.environ, {
                'TCMS_PRODUCT_VERSION': 'v.Test',
        }, True):
            version_id, version_val = self.backend.get_version_id(0)
            self.assertEqual(version_id, 5)
            self.assertEqual(version_val, 'v.Test')
            self.backend.rpc.Version.create.assert_called_with({
                'product': 0,
                'value': 'v.Test'})
