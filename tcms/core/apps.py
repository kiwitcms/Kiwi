# pylint: disable=import-outside-toplevel
from django.apps import AppConfig as DjangoAppConfig
from django.core.checks import register


class AppConfig(DjangoAppConfig):
    name = "tcms.core"

    def ready(self):
        from tcms.core import checks

        register(checks.check_installation_id)
