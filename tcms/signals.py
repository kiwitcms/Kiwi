"""
Defines custom signals sent throught out Kiwi TCMS. You can connect your own
handlers if you'd like to augment some of the default behavior!

If you simply want to connect a signal handler add the following code to your
``local_settings.py``::

    from tcms.signals import *

    user_registered.connect(notify_admins)

In case you want to perform more complex signal handling we advise you to create
a new Django app and connect your handler function(s) to the desired signals
inside the
`AppConfig.ready
<https://docs.djangoproject.com/en/2.0/ref/applications/#django.apps.AppConfig.ready>`_
method. When you are done connect your Django app to the rest of Kiwi TCMS by
altering the following setting::

    INSTALLED_APPS += ['my_custom_app']


.. data:: user_registered

    Sent when a new user is registered into Kiwi TCMS through any of the
    backends which support user registration. The signal receives three keyword
    parameters: ``request``, ``user`` and ``backend`` respectively!
"""

from django.dispatch import Signal

user_registered = Signal(providing_args=['user', 'backend'])


def notify_admins(sender, **kwargs):
    """
        Very simple signal handler which sends emails to site
        admins when a new user has been registered!

        .. warning::

            This handler isn't connected to the ``user_registered`` signal by default!
    """
    from django.urls import reverse
    from django.conf import settings
    from django.utils.translation import ugettext_lazy as _

    from .core.utils.mailto import mailto
    from .core.utils import request_host_link

    request = kwargs.get('request')
    user = kwargs.get('user')

    admin_emails = []
    for name, email in settings.ADMINS:
        admin_emails.append(email)

    user_url = request_host_link(request) + reverse('admin:auth_user_change', args=[user.pk])

    mailto(
        template_name='email/user_registered/notify_admins.txt',
        recipients=admin_emails,
        subject=str(_('New user awaiting approval')),
        context={
            'user': user,
            'user_url': user_url,
        }
    )
