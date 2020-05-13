from io import StringIO

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.test import TestCase


class TestSetDomainCommand(TestCase):
    """Test manage.py set_domain command"""

    def test_without_params_returns_domain(self):
        """Test command without params returns current domain"""
        out = StringIO()
        call_command('set_domain', stdout=out)
        self.assertEqual(
            '127.0.0.1:8000\n',
            out.getvalue())

    def test_set_domain(self):
        """Test if command sets the domain correctly"""
        out = StringIO()
        newdomain = "kiwi.test.bogus:1234"
        call_command('set_domain', newdomain, stdout=out)
        site = Site.objects.get(id=settings.SITE_ID)
        self.assertEqual(newdomain, site.domain)
        self.assertEqual('Kiwi TCMS', site.name)
