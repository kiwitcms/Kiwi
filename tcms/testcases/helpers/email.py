# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _

from tcms.core.history import history_email_for
from tcms.core.utils.mailto import mailto


def email_case_created(case):
    recipients = get_case_notification_recipients(case)
    if not recipients:
        return
    cc_list = case.emailing.get_cc_list()

    subject = _("NEW: TestCase #%(pk)d - %(summary)s") % {
        "pk": case.pk,
        "summary": case.summary,
    }

    body = (
        _(
            """Test case %(pk)d has been created.

### Basic information ###
Summary: %(summary)s

Product: %(product)s
Category: %(category)s
Priority: %(priority)s

Default tester: %(default_tester)s
Text:
%(text)s"""
        )
        % {
            "pk": case.pk,
            "summary": case.summary,
            "product": case.category.product.name,
            "category": case.category.name,
            "priority": case.priority.value,
            "default_tester": case.default_tester,
            "text": case.text,
        }
    )

    mailto(None, subject, recipients, body, cc=cc_list)


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

    if case.emailing.auto_to_case_author and case.author.is_active:
        recipients.add(case.author.email)

    if (
        case.emailing.auto_to_case_tester
        and case.default_tester
        and case.default_tester.is_active
    ):
        recipients.add(case.default_tester.email)

    if case.emailing.auto_to_run_manager:
        managers = case.executions.filter(run__manager__is_active=True).values_list(
            "run__manager__email", flat=True
        )
        recipients.update(managers)  # pylint: disable=objects-update-used

    if case.emailing.auto_to_run_tester:
        run_testers = case.executions.filter(
            run__default_tester__is_active=True
        ).values_list("run__default_tester__email", flat=True)
        recipients.update(run_testers)  # pylint: disable=objects-update-used

    if case.emailing.auto_to_execution_assignee:
        assignees = case.executions.filter(assignee__is_active=True).values_list(
            "assignee__email", flat=True
        )
        recipients.update(assignees)  # pylint: disable=objects-update-used

    # don't email author of last change
    recipients.discard(getattr(case.history.latest().history_user, "email", ""))
    return list(filter(None, recipients))
