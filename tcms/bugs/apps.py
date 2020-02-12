# pylint: disable=import-outside-toplevel
from django.apps import AppConfig as DjangoAppConfig


class AppConfig(DjangoAppConfig):
    name = 'tcms.bugs'

    def ready(self):
        from django.db.models.signals import post_save
        from .models import Bug
        from tcms import signals

        post_save.connect(signals.handle_emails_post_bug_save, sender=Bug)
