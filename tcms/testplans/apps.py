from django.apps import AppConfig as DjangoAppConfig


class AppConfig(DjangoAppConfig):
    name = 'tcms.testplans'

    def ready(self):
        from django.db.models.signals import post_save, pre_save
        from .models import TestPlan
        from tcms import signals

        pre_save.connect(signals.pre_save_clean, TestPlan)
        post_save.connect(signals.handle_emails_post_plan_save, TestPlan)
