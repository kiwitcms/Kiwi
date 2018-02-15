from django.apps import AppConfig as DjangoAppConfig


class AppConfig(DjangoAppConfig):
    name = 'tcms.testcases'

    def ready(self):
        from django.db.models.signals import post_save, pre_delete, pre_save
        from .models import TestCase
        from tcms import signals

        pre_save.connect(signals.pre_save_clean, TestCase)
        post_save.connect(signals.handle_emails_post_case_save, TestCase)
        pre_delete.connect(signals.handle_emails_pre_case_delete, TestCase)
