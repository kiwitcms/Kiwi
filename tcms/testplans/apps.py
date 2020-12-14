# pylint: disable=import-outside-toplevel
from django.apps import AppConfig as DjangoAppConfig


class AppConfig(DjangoAppConfig):
    name = "tcms.testplans"

    def ready(self):
        from django.db.models.signals import post_save, pre_delete, pre_save

        from tcms import signals

        from .models import TestPlan

        pre_save.connect(signals.pre_save_clean, TestPlan)
        post_save.connect(signals.handle_emails_post_plan_save, TestPlan)
        post_save.connect(signals.handle_attachments_post_save, sender=TestPlan)
        pre_delete.connect(signals.handle_attachments_pre_delete, sender=TestPlan)
