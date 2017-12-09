# -*- coding: utf-8 -*-

from tcms.testcases.helpers import email


def on_case_save(sender, instance, created=False, **kwargs):
    # case update and email
    if not created:
        if instance.emailing.notify_on_case_update:
            email.email_case_update(instance)


def on_case_delete(sender, instance, **kwags):
    # case delete and email
    if instance.emailing.notify_on_case_delete:
        email.email_case_deletion(instance)


def pre_save_clean(sender, **kwargs):
    instance = kwargs['instance']
    instance.clean()
