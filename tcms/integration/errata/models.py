# -*- coding: utf-8 -*-
from django.conf import settings
from django.db.models.signals import post_save, post_delete

from tcms.testcases.models import TestCaseBug
from tcms.testruns.models import TestRun, TestCaseRun
from tcms.integration.errata.signals import testrun_created_handler
from tcms.integration.errata.signals import testrun_progress_handler
from tcms.integration.errata.signals import bug_added_handler
from tcms.integration.errata.signals import bug_removed_handler

# Disable producing progress info to consumers (only errata now) by default.
# Set ENABLE_QPID = True in product.py to reopen it.
if settings.ENABLE_QPID:
    # testrun create listen for qpid
    post_save.connect(testrun_created_handler, sender=TestRun)
    # testrun progress listen for qpid
    post_save.connect(
        testrun_progress_handler,
        sender=TestCaseRun,
        dispatch_uid="tcms.testruns.signals.testrun_progress_handler",
    )

    # Bug add/remove listen for qpid
    post_save.connect(bug_added_handler, TestCaseBug)
    post_delete.connect(bug_removed_handler, TestCaseBug)
