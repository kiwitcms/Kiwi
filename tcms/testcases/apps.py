from django.apps import AppConfig as DjangoAppConfig


class AppConfig(DjangoAppConfig):
    name = 'tcms.testcases'

    def ready(self):
        from django.db.models.signals import post_save, post_delete, pre_save
        from .models import TestCase
        from . import signals

        pre_save.connect(signals.pre_save_clean, TestCase)
        post_save.connect(signals.on_case_save, TestCase)
        post_delete.connect(signals.on_case_delete, TestCase)
