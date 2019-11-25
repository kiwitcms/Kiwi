.. _configuration:

Kiwi TCMS configuration settings
================================

All sensible settings are defined in ``tcms/settings/common.py``. You will have
to update some of them for your particular production environment.

.. note::

    After adjusting settings for your environment you have to configure
    Kiwi TCMS via its web interface! As a minimum you have to
    :ref:`configure-kiwi-base-url` and :ref:`configure-bug-trackers`!

.. note::

    Additional information how to override Kiwi TCMS behavior can be found at
    `<http://kiwitcms.org/blog/tags/customization/>`_!

.. literalinclude:: ../../tcms/settings/common.py
   :language: python


Augmenting behavior with signal handlers
----------------------------------------

Kiwi TCMS defines signals which are triggered during specific events.
Administrators may override the default handlers and/or connect additional
ones to augment the default behavior of Kiwi TCMS. For more information
refer to :mod:`tcms.signals`.


Time zone settings
------------------

By default Kiwi TCMS is configured to use the ``UTC`` time zone.
``/etc/localtime`` inside the docker image also points to
``/usr/share/zoneinfo/Etc/UTC``!

The settings which control this behavior are:

- ``USE_TZ`` - controls whether or not Django uses timezone-aware
  datetime objects internally. Can also be controlled via ``KIWI_USE_TZ``
  environment variable
- ``TIME_ZONE`` - a string representing the time zone for this application.
  This should match the actual configuration of your server/docker container!
  Can also be controlled via ``KIWI_TIME_ZONE`` environment variable.


Your server/docker container clock should also match the accurate time of day!

.. important::

    Unlike language there is no way to automatically receive time zone
    information from the browser and display different values for users.
    Instead Kiwi TCMS displays the current server time & time zone in the
    navigation bar! All other timestamps are in the same time zone!


Using Amazon SES instead of SMTP email
--------------------------------------

Kiwi TCMS supports email notifications which by default are sent over SMTP and
need to be configured via the following settings::

    # standard Django settings
    EMAIL_HOST = 'smtp.example.com'
    EMAIL_PORT = 25
    DEFAULT_FROM_EMAIL = 'kiwi@example.com'

    # additional Kiwi TCMS setting
    EMAIL_SUBJECT_PREFIX = '[Kiwi-TCMS] '

If you'd like to use an external email service, like Amazon SES you also need
to configure the following settings::


    EMAIL_BACKEND = 'django_ses.SESBackend'
    AWS_SES_ACCESS_KEY_ID = 'xxxxxxxxxxxxxxxxxxxx'
    AWS_SES_SECRET_ACCESS_KEY = 'YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY'

Also modify ``Dockerfile`` to include the following lines::

    RUN pip install django_ses


Kerberos authentication
-----------------------

See
`kiwitcms-auth-kerberos <https://github.com/kiwitcms/kiwitcms-auth-kerberos>`_.


Public read-only access
-----------------------

By default Kiwi TCMS requires all users to be logged in. This is achieved via
``global_login_required.GlobalLoginRequiredMiddleware``. If you wish to allow
public read-only access to certain pages (Search, TestCase view, TestPlan view,
etc) simply disable this middleware. Add the following to
your ``local_settings.py``::

    from django.conf import settings

    settings.MIDDLEWARE.remove('global_login_required.GlobalLoginRequiredMiddleware')
