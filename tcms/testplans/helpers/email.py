# -*- coding: utf-8 -*-
from django.conf import settings

from tcms.core.utils.mailto import mailto


def email_plan_update(plan):
    recipients = get_plan_notification_recipients(plan)
    if not recipients:
        return
    subject = u'TestPlan %s has been updated.' % plan.pk
    mailto(settings.PLAN_EMAIL_TEMPLATE, subject,
           recipients, {'plan': plan})


def get_plan_notification_recipients(plan):
    recipients = set()
    if plan.owner:
        if plan.emailing.auto_to_plan_owner:
            recipients.add(plan.owner.email)
    if plan.emailing.auto_to_plan_author:
        recipients.add(plan.author.email)
    if plan.emailing.auto_to_case_owner:
        case_authors = plan.case.values_list('author__email', flat=True)
        recipients.update(case_authors)  # pylint: disable=objects-update-used
    if plan.emailing.auto_to_case_default_tester:
        case_testers = plan.case.values_list('default_tester__email',
                                             flat=True)
        recipients.update(case_testers)  # pylint: disable=objects-update-used
    return list(filter(lambda e: bool(e), recipients))
