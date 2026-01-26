# -*- coding: utf-8 -*-
import threading

from django.conf import settings
from django.core.mail import send_mail
from django.forms import ValidationError
from django.template.loader import render_to_string
from django.utils.translation import override


def custom_email_validators(email):
    for validator in getattr(settings, "EMAIL_VALIDATORS", ()):
        validator(email)


def remove_invalid_address(address):
    try:
        custom_email_validators(address)
    except ValidationError:
        return False

    return True


@override(settings.LANGUAGE_CODE)
def mailto(  # pylint: disable=invalid-name
    template_name,
    subject,
    recipients=None,
    context=None,
    cc=None,
):
    # no multi-line email headers
    subject = subject.replace("\n", " ").replace("\r", " ")

    # make a list with recipients and filter out duplicates
    if isinstance(recipients, list):
        recipients = list(set(recipients))
    else:
        recipients = [recipients]
    recipients.sort()

    # extend with the CC list
    if cc:
        recipients.extend(cc)

    # if debugging then send to ADMINS as well
    if settings.DEBUG:
        for _, admin_email in settings.ADMINS:
            recipients.append(admin_email)

    # filter out invalid email addresses, e.g. black-listed ones
    recipients = list(filter(remove_invalid_address, recipients))
    if not recipients:
        return

    # this is a workaround to allow passing body text directly
    if template_name:
        body = render_to_string(template_name, context)
    else:
        body = context

    sender = settings.DEFAULT_FROM_EMAIL
    email_thread = threading.Thread(
        target=send_mail,
        args=(settings.EMAIL_SUBJECT_PREFIX + subject, body, sender, recipients),
        kwargs={"fail_silently": False},
        daemon=True,
    )
    email_thread.start()
