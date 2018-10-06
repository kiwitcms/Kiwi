from django.apps import AppConfig as DjangoAppConfig


class AppConfig(DjangoAppConfig):
    name = 'tcms.testruns'

    def ready(self):
        from django.db.models.signals import post_save, pre_save
        from .models import TestRun
        from tcms import signals

        post_save.connect(signals.handle_emails_post_run_save, sender=TestRun)
        pre_save.connect(signals.pre_save_clean, sender=TestRun)
