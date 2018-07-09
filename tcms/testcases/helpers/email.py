# -*- coding: utf-8 -*-
from django.conf import settings

from tcms.core.utils.mailto import mailto


def email_case_update(case):
    recipients = get_case_notification_recipients(case)
    if not recipients:
        return
    cc = case.emailing.get_cc_list()
    subject = 'TestCase %s has been updated.' % case.pk
    txt = case.latest_text()
    context = {
        'test_case': case, 'test_case_text': txt,
    }
    template = settings.CASE_EMAIL_TEMPLATE
    mailto(template, subject, recipients, context, cc=cc)


def email_case_deletion(case):
    recipients = get_case_notification_recipients(case)
    cc = case.emailing.get_cc_list()
    if not recipients:
        return
    subject = 'TestCase %s has been deleted.' % case.pk
    context = {
        'case': case,
    }
    template = settings.CASE_EMAIL_TEMPLATE
    mailto(template, subject, recipients, context, cc=cc)


def get_case_notification_recipients(case):
    recipients = set()
    if case.emailing.auto_to_case_author:
        recipients.add(case.author.email)
    if case.emailing.auto_to_case_tester and case.default_tester:
        recipients.add(case.default_tester.email)
    if case.emailing.auto_to_run_manager:
        managers = case.case_run.values_list('run__manager__email', flat=True)
        recipients.update(managers)  # pylint: disable=objects-update-used
    if case.emailing.auto_to_run_tester:
        run_testers = case.case_run.values_list('run__default_tester__email',
                                                flat=True)
        recipients.update(run_testers)  # pylint: disable=objects-update-used
    if case.emailing.auto_to_case_run_assignee:
        assignees = case.case_run.values_list('assignee__email', flat=True)
        recipients.update(assignees)  # pylint: disable=objects-update-used
    return list(filter(lambda e: bool(e), recipients))
