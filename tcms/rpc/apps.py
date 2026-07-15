# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

# pylint: disable=import-outside-toplevel
from django.apps import AppConfig as DjangoAppConfig


class AppConfig(DjangoAppConfig):
    name = "tcms.rpc"

    def ready(self):
        import importlib

        from django.conf import settings

        for module_path in settings.MODERNRPC_METHODS_MODULES:
            importlib.import_module(module_path)
