# pylint: disable=unused-argument, import-outside-toplevel
"""
Defines custom signals sent throughout Kiwi TCMS. You can connect your own
handlers if you'd like to augment some of the default behavior!

If you simply want to connect a signal handler add the following code to your
``local_settings.py``::

    from tcms.signals import *

    USER_REGISTERED_SIGNAL.connect(notify_admins)

In case you want to perform more complex signal handling we advise you to create
a new Django app and connect your handler function(s) to the desired signals
inside the
`AppConfig.ready
<https://docs.djangoproject.com/en/2.2/ref/applications/#django.apps.AppConfig.ready>`_
method. When you are done connect your Django app to the rest of Kiwi TCMS by
altering the following setting::

    INSTALLED_APPS += ['my_custom_app']
"""
from django.db.models import ObjectDoesNotExist
from django.dispatch import Signal
from django.utils.translation import gettext_lazy as _

__all__ = [
    "USER_REGISTERED_SIGNAL",
    "notify_admins",
    "pre_save_clean",
    "handle_attachments_pre_delete",
    "handle_attachments_post_save",
    "handle_comments_pre_delete",
    "handle_emails_post_case_save",
    "handle_emails_pre_case_delete",
    "handle_emails_post_plan_save",
    "handle_emails_post_run_save",
    "handle_emails_post_bug_save",
]


#: Sent when a new user is registered into Kiwi TCMS. This signal receives two
#: keyword parameters: ``request`` and ``user`` respectively!
USER_REGISTERED_SIGNAL = Signal()


def notify_admins(sender, **kwargs):
    """
    Very simple signal handler which sends emails to site
    admins when a new user has been registered!

    .. warning::

        This handler isn't connected to the ``USER_REGISTERED_SIGNAL`` by default!
    """
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.urls import reverse

    from tcms.core.utils import request_host_link
    from tcms.core.utils.mailto import mailto

    if kwargs.get("raw", False):
        return

    admin_emails = set()
    # super-users can approve others
    for super_user in get_user_model().objects.filter(is_superuser=True):
        admin_emails.add(super_user.email)
    # site admins should be able to do so as well
    for _name, email in settings.ADMINS:
        admin_emails.add(email)

    request = kwargs.get("request")
    user = kwargs.get("user")
    user_url = request_host_link(request) + reverse(
        "admin:auth_user_change", args=[user.pk]
    )

    mailto(
        template_name="email/user_registered/notify_admins.txt",
        recipients=list(admin_emails),
        subject=str(_("New user awaiting approval")),
        context={
            "username": user.username,
            "user_url": user_url,
        },
    )


def handle_emails_post_case_save(sender, instance, created=False, **kwargs):
    """
    Send email updates after a TestCase has been updated!
    """
    if kwargs.get("raw", False):
        return

    if not created and instance.emailing.notify_on_case_update:
        from tcms.testcases.helpers import email

        email.email_case_update(instance)


def handle_emails_pre_case_delete(sender, **kwargs):
    """
    Send email updates before a TestCase will be deleted!
    """
    if kwargs.get("raw", False):
        return

    instance = kwargs["instance"]

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
    if kwargs.get("raw", False):
        return

    instance = kwargs["instance"]
    instance.clean()


def handle_emails_post_plan_save(sender, instance, created=False, **kwargs):
    """
    Send email updates after a TestPlan has been updated!
    """
    if kwargs.get("raw", False):
        return

    if not created and instance.emailing.notify_on_plan_update:
        from tcms.testplans.helpers import email

        email.email_plan_update(instance)


def handle_emails_post_run_save(sender, *_args, **kwargs):
    """
    Send email updates after a TestRus has been created or updated!
    """
    from tcms.core.history import history_email_for
    from tcms.core.utils.mailto import mailto

    if kwargs.get("raw", False):
        return

    instance = kwargs["instance"]

    if kwargs.get("created"):
        template_name = "email/post_run_save/email.txt"
        subject = _("NEW: TestRun #%(pk)d - %(summary)s") % {
            "pk": instance.pk,
            "summary": instance.summary,
        }
        context = {"test_run": instance}
    else:
        template_name = None
        subject, context = history_email_for(instance, instance.summary)

    mailto(template_name, subject, instance.get_notify_addrs(), context)


def handle_attachments_pre_delete(sender, **kwargs):
    """
    Delete files attached to object which is about to be
    deleted b/c django-attachments' object_id is not a FK relationship
    and we can't rely on cascading delete!
    """
    from attachments.models import Attachment
    from attachments.views import remove_file_from_disk

    if kwargs.get("raw", False):
        return

    instance = kwargs["instance"]

    attached_files = Attachment.objects.attachments_for_object(instance)
    for attachment in attached_files:
        remove_file_from_disk(attachment.attachment_file)
    attached_files.delete()


def handle_comments_pre_delete(sender, **kwargs):
    """
    Delete comments attached to object which is about to be
    deleted b/c django-comments' object_pk is not a FK relationship
    and we can't rely on cascading delete!
    """
    from tcms.core.helpers.comments import get_comments

    if kwargs.get("raw", False):
        return

    instance = kwargs["instance"]

    get_comments(instance).delete()


def handle_emails_post_bug_save(sender, instance, created=False, **kwargs):
    """
    Send email updates to assignee after they've been
    assigned a bug on bug creation.
    """
    if not created or instance.assignee is None:
        return

    from tcms.core.utils.mailto import mailto

    mailto(
        template_name="email/post_bug_save/email.txt",
        recipients=[instance.assignee.email],
        subject=_("NEW: Bug #%(pk)d - %(summary)s")
        % {"pk": instance.pk, "summary": instance.summary},
        context={"bug": instance},
    )


def _introspect_request():
    """
    Introspect the current thread b/c signals are executed synchronously
    after .save() and find out the `request` variable.
    """
    import inspect

    for frame_record in inspect.stack():
        if frame_record[3] == "get_response":
            return frame_record[0].f_locals["request"]

    return None


def handle_attachments_post_save(sender, instance, created=False, **kwargs):
    """
    SimpleMDE image/file buttons will upload attachments under the currently
    logged-in user. This signal handler will re-attach these files under the
    document which is being saved!
    """
    from attachments.models import Attachment

    if kwargs.get("raw", False):
        return

    request = _introspect_request()
    if not request:
        return

    for attachment in Attachment.objects.attachments_for_object(request.user):
        attachment.attach_to(instance)
