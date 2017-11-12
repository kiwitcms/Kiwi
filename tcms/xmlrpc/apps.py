# -*- coding: utf-8 -*-

import os

from django.apps import AppConfig as DjangoAppConfig
from django.utils.translation import ugettext_lazy as _

from tcms.xmlrpc.filters import autowrap_xmlrpc_apis

xmlrpc_module_path = os.path.dirname(__file__)


class AppConfig(DjangoAppConfig):
    label = name = 'tcms.xmlrpc'
    verbose_name = _("Nitrate XMLRPC APIs")

    def ready(self):
        autowrap_xmlrpc_apis(xmlrpc_module_path, __package__)
