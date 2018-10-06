Kiwi TCMS configuration settings
================================

All sensible settings are defined in ``tcms/settings/common.py``. You will have
to update some of them for your particular production environment.

.. note::

    After adjusting settings for your environment you have to configure
    Kiwi TCMS via its web interface! As a minimum you have to
    :ref:`configure-kiwi-base-url` and :ref:`configure-bug-trackers`!

.. literalinclude:: ../../tcms/settings/common.py
   :language: python

.. note::

    Additional information how to override the defaults can be found at
    `<http://kiwitcms.org/blog/tags/customization/>`_!


Augmenting behavior with signal handlers
----------------------------------------

Kiwi TCMS defines signals which are triggered during specific events.
Administrators may override the default handlers and/or connect additional
ones to augment the default behavior of Kiwi TCMS. For more information
refer to :mod:`tcms.signals`.


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

If you'd like to use an external email service, like Amazon SES you also need to
configure the following settings::


    EMAIL_BACKEND = 'django_ses.SESBackend'
    AWS_SES_ACCESS_KEY_ID = 'xxxxxxxxxxxxxxxxxxxx'
    AWS_SES_SECRET_ACCESS_KEY = 'YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY'

Also modify ``Dockerfile`` to include the following lines::

    RUN pip install django_ses


Bugzilla authentication
-----------------------

See
`kiwitcms-auth-bugzilla <https://github.com/kiwitcms/kiwitcms-auth-bugzilla>`_.


Kerberos authentication
-----------------------

See
`kiwitcms-auth-kerberos <https://github.com/kiwitcms/kiwitcms-auth-kerberos>`_.
