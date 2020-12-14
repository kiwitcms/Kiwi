# pylint: disable=import-outside-toplevel

from django.apps import AppConfig as DjangoAppConfig


class AppConfig(DjangoAppConfig):
    name = "tcms.testcases"

    def ready(self):
        from django.db.models.signals import post_save, pre_delete, pre_save

        from tcms import signals

        from .models import TestCase

        pre_save.connect(signals.pre_save_clean, TestCase)
        post_save.connect(signals.handle_emails_post_case_save, TestCase)
        post_save.connect(signals.handle_attachments_post_save, sender=TestCase)
        pre_delete.connect(signals.handle_emails_pre_case_delete, TestCase)
        pre_delete.connect(signals.handle_attachments_pre_delete, sender=TestCase)
        pre_delete.connect(signals.handle_comments_pre_delete, TestCase)
