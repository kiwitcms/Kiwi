# -*- coding: utf-8 -*-
from tcms.core.history import history_email_for
from tcms.core.utils.mailto import mailto


def email_plan_update(plan):
    recipients = get_plan_notification_recipients(plan)
    if not recipients:
        return
    subject, body = history_email_for(plan, plan.name)
    mailto(None, subject, recipients, body)


def get_plan_notification_recipients(plan):  # pylint: disable=invalid-name
    recipients = set()

    if plan.author and plan.emailing.auto_to_plan_author:
        recipients.add(plan.author.email)

    if plan.emailing.auto_to_case_owner:
        case_authors = plan.cases.values_list("author__email", flat=True)
        recipients.update(case_authors)  # pylint: disable=objects-update-used

    if plan.emailing.auto_to_case_default_tester:
        case_testers = plan.cases.values_list("default_tester__email", flat=True)
        recipients.update(case_testers)  # pylint: disable=objects-update-used

    # don't email author of last change
    recipients.discard(getattr(plan.history.latest().history_user, "email", ""))
    return list(filter(bool, recipients))
