# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

import pkg_resources
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.urls.resolvers import URLResolver
from django.utils.translation import gettext_lazy as _

from tcms.telemetry.tests.plugin import menu as plugin_menu
from tcms.urls import urlpatterns


class PluginDiscoveryTestCase(TestCase):
    def test_installed_apps_is_updated(self):
        """
            Given there are some plugins installed
            Then validate the plugin module is added to INSTALLED_APPS
        """
        for plugin in pkg_resources.iter_entry_points('kiwitcms.plugins'):
            self.assertIn(plugin.module_name, settings.INSTALLED_APPS)


class UrlDiscoveryTestCase(TestCase):
    def test_urlpatterns_is_updated(self):
        """
            Given there are some plugins installed
            Then validate urlpatterns:

                - ^<plugin-name>/ includes(<plugin-module-urls>)
        """
        for plugin in pkg_resources.iter_entry_points('kiwitcms.plugins'):
            for url_resolver in urlpatterns:
                if isinstance(url_resolver, URLResolver):
                    if str(url_resolver.pattern) == '^%s/' % plugin.name and \
                            url_resolver.urlconf_module.__name__ == plugin.module_name+'.urls':
                        return

        self.fail('No plugins found or urlpatterns not valid')


class MenuDiscoveryTestCase(TestCase):
    def test_menu_is_updated(self):
        """
            Given there are some plugins installed
            Then navigation menu under PLUGINS will be extended
        """
        for name, target in settings.MENU_ITEMS:
            if name == _('PLUGINS'):
                for menu_item in plugin_menu.MENU_ITEMS:
                    self.assertIn(menu_item, target)

                return

        self.fail('PLUGINS not found in settings.MENU_ITEMS')

    def test_menu_rendering(self):
        """
            Given there are some plugins installed
            Then navigation menu under PLUGINS will be rendered
                with several levels of sub menus.
        """
        response = self.client.get(reverse('iframe-navigation'))
        self.assertContains(response, 'Fake Telemetry plugin')
        self.assertContains(
            response,
            "<a class='dropdown-toggle' href='#' data-toggle='dropdown'>Fake Plugin sub-menu</a>",
            html=True)
        self.assertContains(response,
                            '<a href="/a_fake_plugin/example/" target="_parent">Example</a>',
                            html=True)
        self.assertContains(
            response,
            "<a class='dropdown-toggle' href='#' data-toggle='dropdown'>3rd level menu</a>",
            html=True)
        self.assertContains(response, 'Go to Dashboard')
        self.assertContains(response, 'Go to kiwitcms.org')
