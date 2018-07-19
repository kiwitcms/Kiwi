from django.apps import AppConfig as DjangoAppConfig


class AppConfig(DjangoAppConfig):
    name = 'tcms.testruns'

    def ready(self):
        from django.db.models.signals import post_save, post_delete, pre_save
        from .models import TestRun, TestCaseRun
        from tcms import signals

        post_save.connect(signals.handle_emails_post_run_save, sender=TestRun)
        post_save.connect(signals.handle_post_case_run_save, sender=TestCaseRun,
                          dispatch_uid='tcms.testruns.models.TestCaseRun')
        post_delete.connect(signals.handle_post_case_run_delete, sender=TestCaseRun,
                            dispatch_uid='tcms.testruns.models.TestCaseRun')
        pre_save.connect(signals.pre_save_clean, sender=TestRun)
