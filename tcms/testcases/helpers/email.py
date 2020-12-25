# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _

from tcms.core.history import history_email_for
from tcms.core.utils.mailto import mailto


def email_case_update(case):
    recipients = get_case_notification_recipients(case)
    if not recipients:
        return
    cc_list = case.emailing.get_cc_list()
    subject, body = history_email_for(case, case.summary)
    mailto(None, subject, recipients, body, cc=cc_list)


def email_case_deletion(case):
    recipients = get_case_notification_recipients(case)
    cc_list = case.emailing.get_cc_list()
    if not recipients:
        return
    subject = _("DELETED: TestCase #%(pk)d - %(summary)s") % {
        "pk": case.pk,
        "summary": case.summary,
    }
    context = {"case": case}
    mailto("email/post_case_delete/email.txt", subject, recipients, context, cc=cc_list)


def get_case_notification_recipients(case):
    recipients = set()

    if case.emailing.auto_to_case_author:
        recipients.add(case.author.email)

    if case.emailing.auto_to_case_tester and case.default_tester:
        recipients.add(case.default_tester.email)

    if case.emailing.auto_to_run_manager:
        managers = case.executions.values_list("run__manager__email", flat=True)
        recipients.update(managers)  # pylint: disable=objects-update-used

    if case.emailing.auto_to_run_tester:
        run_testers = case.executions.values_list(
            "run__default_tester__email", flat=True
        )
        recipients.update(run_testers)  # pylint: disable=objects-update-used

    if case.emailing.auto_to_execution_assignee:
        assignees = case.executions.values_list("assignee__email", flat=True)
        recipients.update(assignees)  # pylint: disable=objects-update-used

    # don't email author of last change
    recipients.discard(getattr(case.history.latest().history_user, "email", ""))
    return list(filter(None, recipients))
