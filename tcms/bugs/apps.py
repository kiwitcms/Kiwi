# pylint: disable=import-outside-toplevel
from django.apps import AppConfig as DjangoAppConfig
from django.db.models.signals import post_migrate
from django.db.models.signals import post_save


class AppConfig(DjangoAppConfig):
    name = 'tcms.bugs'

    def ready(self):
        from .models import Bug
        from .management import create_permissions
        from tcms import signals

        post_save.connect(signals.handle_emails_post_bug_save, sender=Bug)
        post_migrate.connect(
            create_permissions,
            dispatch_uid="tcms.bugs.management.create_permissions"
        )
