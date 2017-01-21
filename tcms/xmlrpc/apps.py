from django.apps import AppConfig as DjangoAppConfig
from django.utils.translation import ugettext_lazy as _


class AppConfig(DjangoAppConfig):
    label = name = 'tcms.xmlrpc'
    verbose_name = _("Nitrate XMLRPC APIs")
