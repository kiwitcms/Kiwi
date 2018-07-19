# pylint: disable=unused-argument
"""
Defines custom signals sent throught out Kiwi TCMS. You can connect your own
handlers if you'd like to augment some of the default behavior!

If you simply want to connect a signal handler add the following code to your
``local_settings.py``::

    from tcms.signals import *

    USER_REGISTERED_SIGNAL.connect(notify_admins)

In case you want to perform more complex signal handling we advise you to create
a new Django app and connect your handler function(s) to the desired signals
inside the
`AppConfig.ready
<https://docs.djangoproject.com/en/2.0/ref/applications/#django.apps.AppConfig.ready>`_
method. When you are done connect your Django app to the rest of Kiwi TCMS by
altering the following setting::

    INSTALLED_APPS += ['my_custom_app']
"""
from django.dispatch import Signal
from django.db.models import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _

__all__ = [
    'USER_REGISTERED_SIGNAL',

    'notify_admins',
    'pre_save_clean',
    'handle_emails_post_case_save',
    'handle_emails_pre_case_delete',
    'handle_emails_post_plan_save',
    'handle_emails_post_run_save',
    'handle_post_case_run_save',
    'handle_post_case_run_delete',
]


#: Sent when a new user is registered into Kiwi TCMS through any of the
#: backends which support user registration. The signal receives three keyword
#: parameters: ``request``, ``user`` and ``backend`` respectively!
USER_REGISTERED_SIGNAL = Signal(providing_args=['user', 'backend'])


def notify_admins(sender, **kwargs):
    """
        Very simple signal handler which sends emails to site
        admins when a new user has been registered!

        .. warning::

            This handler isn't connected to the ``USER_REGISTERED_SIGNAL`` by default!
    """
    from django.urls import reverse
    from django.conf import settings

    from tcms.core.utils.mailto import mailto
    from tcms.core.utils import request_host_link

    request = kwargs.get('request')
    user = kwargs.get('user')

    admin_emails = []
    for _name, email in settings.ADMINS:
        admin_emails.append(email)

    user_url = request_host_link(request) + reverse('admin:auth_user_change', args=[user.pk])

    mailto(
        template_name='email/user_registered/notify_admins.txt',
        recipients=admin_emails,
        subject=str(_('New user awaiting approval')),
        context={
            'username': user.username,
            'user_url': user_url,
        }
    )


def handle_emails_post_case_save(sender, instance, created=False, **_kwargs):
    """
        Send email updates after a TestCase has been updated!
    """
    if not created:
        if instance.emailing.notify_on_case_update:
            from tcms.testcases.helpers import email
            email.email_case_update(instance)


def handle_emails_pre_case_delete(sender, **kwargs):
    """
        Send email updates before a TestCase will be deleted!
    """
    instance = kwargs['instance']

    try:
        # note: using the `email_settings` related object instead of the
        # `emailing` property b/c it breaks with cascading deletes via admin.
        # if there are not settings created before hand they default to False
        # so email will not going to be sent and the exception is safe to ignore
        if instance.email_settings.notify_on_case_delete:
            from tcms.testcases.helpers import email
            email.email_case_deletion(instance)
    except ObjectDoesNotExist:
        pass


def pre_save_clean(sender, **kwargs):
    instance = kwargs['instance']
    instance.clean()


def handle_emails_post_plan_save(sender, instance, created=False, **_kwargs):
    """
        Send email updates after a TestPlan has been updated!
    """
    if not created:
        if instance.emailing.notify_on_plan_update:
            from tcms.testplans.helpers import email
            email.email_plan_update(instance)


def handle_emails_post_run_save(sender, *_args, **kwargs):
    """
        Send email updates after a TestRus has been created or updated!
    """
    from tcms.core.utils.mailto import mailto

    instance = kwargs['instance']

    if kwargs.get('created'):
        subject = _('New TestRun %(summary)s created') % {'summary': instance.summary}
    else:
        subject = _('TestRun %(summary)s has been updated') % {'summary': instance.summary}

    mailto(template_name='email/post_run_save/email.txt',
           subject=subject,
           recipients=instance.get_notify_addrs(),
           context={'test_run': instance})


def handle_post_case_run_save(sender, *_args, **kwargs):
    """
        Auto-update TestRun status after TestCaseRun is created!
    """
    # TODO: does this work properly
    instance = kwargs['instance']
# todo: what about after update ????
    if kwargs.get('created'):
        instance.run.update_completion_status(is_auto_updated=True)


def handle_post_case_run_delete(sender, **kwargs):
    """
        Auto-update TestRun status after TestCaseRun is deleted!
    """
    # TODO: does this work properly
    instance = kwargs['instance']
    instance.run.update_completion_status(is_auto_updated=True)
