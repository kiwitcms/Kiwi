from django.apps import AppConfig as DjangoAppConfig
from django.utils.translation import ugettext_lazy as _


class AppConfig(DjangoAppConfig):
    label = name = 'tcms.core.contrib.auth'
    verbose_name = _("Core auth")
