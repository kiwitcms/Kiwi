# -*- coding: utf-8 -*-
import threading

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def mailto(template_name, subject, recipients=None,
           context=None, sender=settings.DEFAULT_FROM_EMAIL,
           cc=None):
    # make a list with recipients and filter out duplicates
    if isinstance(recipients, list):
        recipients = list(set(recipients))
    else:
        recipients = [recipients]

    # extend with the CC list
    if cc:
        recipients.extend(cc)

    # if debugging then send to ADMINS as well
    if settings.DEBUG:
        for (admin_name, admin_email) in settings.ADMINS:
            recipients.append(admin_email)

    body = render_to_string(template_name, context)

    email_thread = threading.Thread(
        target=send_mail,
        args=(settings.EMAIL_SUBJECT_PREFIX + subject, body, sender, recipients),
        kwargs={'fail_silently': False}
    )
    # This is to tell Python not to wait for the thread to return
    email_thread.setDaemon(True)
    email_thread.start()
