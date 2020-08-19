# pylint: disable=import-outside-toplevel
from django.apps import AppConfig as DjangoAppConfig
from django.db.models.signals import post_migrate
from django.db.models.signals import post_save
from django.db.models.signals import pre_delete


class AppConfig(DjangoAppConfig):
    name = 'tcms.bugs'

    def ready(self):
        from .models import Bug
        from .management import create_permissions
        from tcms import signals

        post_save.connect(signals.handle_emails_post_bug_save, sender=Bug)
        post_save.connect(signals.handle_attachments_post_save, sender=Bug)
        pre_delete.connect(signals.handle_attachments_pre_delete, sender=Bug)
        pre_delete.connect(signals.handle_comments_pre_delete, sender=Bug)
        post_migrate.connect(
            create_permissions,
            dispatch_uid="tcms.bugs.management.create_permissions"
        )
