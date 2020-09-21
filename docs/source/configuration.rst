.. _configuration:

Kiwi TCMS configuration settings
================================

All sensible settings are defined in ``tcms/settings/common.py``. You will have
to update some of them for your particular production environment.

.. note::

    After adjusting settings for your environment you have to configure
    Kiwi TCMS via its web interface! As a minimum you have to
    :ref:`configure-kiwi-domain` and :ref:`configure-bug-trackers`!

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


Language and emojis
-------------------

By default our ``docker-compose.yml`` file is configured with MariaDB and
uses charset ``utf8mb4`` and collation ``utf8mb4_unicode_ci``. That should
be sufficient to support many languages plus emojis. If you are having troubles
consult `MariaDB Character Sets and Collations <https://mariadb.com/kb/en/character-sets/>`_
documentation.

If you need to change the default settings see ``docker-compose.yml`` or
``/etc/mysql/conf.d/mariadb.cnf`` if using a stand alone DB server! On the
application side see ``DATABASES['default']['OPTIONS']`` in
``tcms/settings/common.py``.


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


.. _email-settings:

E-mail settings
---------------

Kiwi TCMS supports email notifications which by default are sent over SMTP and
need to be configured via the following settings:

- Common settings::

    SERVER_EMAIL = DEFAULT_FROM_EMAIL = 'kiwi@example.com'
    # additional Kiwi TCMS setting
    EMAIL_SUBJECT_PREFIX = '[Kiwi-TCMS] '

- SMTP specific settings::

    EMAIL_HOST = 'smtp.example.com'
    EMAIL_PORT = 25
    EMAIL_HOST_USER = 'smtp_username'
    EMAIL_HOST_PASSWORD = 'smtp_password'

To enable SSL or TLS support include one of the following::

    EMAIL_USE_TLS = True
    EMAIL_USE_SSL = True

For more details refer to Django documentation at https://docs.djangoproject.com/en/3.0/topics/email/


Testing and debugging e-mail configuration
------------------------------------------
Sending test e-mail to one or more addresses::

    docker exec -it kiwi_web /Kiwi/manage.py sendtestemail user1@example1.tld user2@example2.tld ...

More details at: https://docs.djangoproject.com/en/3.0/ref/django-admin/#sendtestemail


Using Amazon SES instead of SMTP email
--------------------------------------

If you'd like to use an external email service, like Amazon SES you need
to configure the following settings too::

    EMAIL_BACKEND = 'django_ses.SESBackend'
    AWS_SES_ACCESS_KEY_ID = 'xxxxxxxxxxxxxxxxxxxx'
    AWS_SES_SECRET_ACCESS_KEY = 'YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY'

Also modify ``Dockerfile`` to include the following lines::

    RUN pip install django_ses


Use reCAPTCHA during registration
---------------------------------

.. versionadded:: 8.7

If you want to use `Google reCAPTCHA <https://www.google.com/recaptcha/admin/>`_
on the registration page then add the following to your settings::

    if 'captcha' not in INSTALLED_APPS:
        INSTALLED_APPS.append('captcha')

        RECAPTCHA_PUBLIC_KEY = '......'
        RECAPTCHA_PRIVATE_KEY = '.....'
        RECAPTCHA_USE_SSL = True

.. important::

    This is not enabled by default because the ``django-recaptcha`` library
    will cause Kiwi TCMS to stop working if the appropriate keys are not
    provided!


Kerberos authentication
-----------------------

See
`kiwitcms-auth-kerberos <https://github.com/kiwitcms/kiwitcms-auth-kerberos>`_.


Anonymous read-only access
--------------------------

.. versionchanged:: 8.7

By default Kiwi TCMS requires :ref:`permissions<managing-permissions>`,
including view permissions which means users must be logged in!
If you wish to allow anonymous read-only access then define the following setting::

    AUTHENTICATION_BACKENDS = [
        'django.contrib.auth.backends.ModelBackend',
        'guardian.backends.ObjectPermissionBackend',
        'tcms.kiwi_auth.backends.AnonymousViewBackend',
    ]

.. versionadded:: 8.7

    ``tcms.kiwi_auth.backends.AnonymousViewBackend`` was added instead of the
    previous ``PUBLIC_VIEWS`` setting.

.. versionchanged:: 8.8

    ``guardian.backends.ObjectPermissionBackend`` was added and the
    ``AUTHENTICATION_BACKENDS`` setting is now explicitly specified!
