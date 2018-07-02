# pylint: disable=invalid-name

from django import test
from django.conf import settings
from django.contrib.auth import load_backend


class TestBackendInterface(test.TestCase):
    """
        Test that all selected authentication backends
        provide the same interface as
        :class:`tcms.core.contrib.auth.backends.DBModelBackend`
    """
    def test_required_class_attributes_are_present(self):
        for backend_path in settings.AUTHENTICATION_BACKENDS:
            backend = load_backend(backend_path)
            self.assertTrue(hasattr(backend, 'can_login'))
            self.assertTrue(hasattr(backend, 'can_logout'))
            self.assertTrue(hasattr(backend, 'can_register'))
