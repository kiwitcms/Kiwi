# pylint: disable=import-outside-toplevel
from django.apps import AppConfig as DjangoAppConfig


class AppConfig(DjangoAppConfig):
    name = "tcms.testruns"

    def ready(self):
        from django.db.models.signals import post_save, pre_delete, pre_save

        from tcms import signals

        from .models import TestExecution, TestRun

        post_save.connect(signals.handle_emails_post_run_save, sender=TestRun)
        post_save.connect(signals.handle_attachments_post_save, sender=TestRun)
        pre_save.connect(signals.pre_save_clean, sender=TestRun)
        pre_delete.connect(signals.handle_attachments_pre_delete, TestRun)

        post_save.connect(signals.handle_attachments_post_save, sender=TestExecution)
        pre_delete.connect(signals.handle_attachments_pre_delete, TestExecution)
        pre_delete.connect(signals.handle_comments_pre_delete, TestExecution)
