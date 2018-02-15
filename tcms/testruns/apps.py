from django.apps import AppConfig as DjangoAppConfig


class AppConfig(DjangoAppConfig):
    name = 'tcms.testruns'

    def ready(self):
        from django.db.models.signals import post_save, post_delete, pre_save
        from tcms.signals import post_update

        from .models import TestRun, TestCaseRun
        from . import signals

        post_save.connect(signals.post_run_saved, sender=TestRun)
        post_save.connect(signals.post_case_run_saved, sender=TestCaseRun,
                          dispatch_uid='tcms.testruns.models.TestCaseRun')
        post_delete.connect(signals.post_case_run_deleted, sender=TestCaseRun,
                            dispatch_uid='tcms.testruns.models.TestCaseRun')
        pre_save.connect(signals.pre_save_clean, sender=TestRun)

        post_update.connect(signals.post_update_handler)
