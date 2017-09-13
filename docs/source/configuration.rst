Kiwi TCMS configuration settings
==================================

All sensible settings are defined in ``tcms/settings/common.py``. You will have
to update some of them for your particular production environment.

.. literalinclude:: ../../tcms/settings/common.py
   :language: python

.. note::

    Information how to override the default settings and Docker image are
    available at `<https://github.com/MrSenko/kiwi-docker>`_!


JIRA options
------------

JIRA integration can be controlled via the ``JIRA_OPTIONS`` configuration
setting. By default this setting is not provided and the code uses
``jira.JIRA.DEFAULT_OPTIONS``.


Integration with GitHub Issues
------------------------------

When configuring a GitHub Issue Tracker you can leave the ``API URL`` and
``API username`` fields empty. The code uses the ``Base URL`` field to figure
out to which repository you want to communicate.

.. important::

    GitHub authentication is performed via token which needs to be configured
    in the ``API password or token`` field!

.. note::

    GitHub does not support displaying multiple issues in a table format like
    Bugzilla and JIRA do. This means that in Test Case Run Report view you will
    see GitHub issues listed one by one and there will not be a link to open all
    of them inside GitHub's interface!


Using Amazon SES instead of SMTP email
--------------------------------------

Kiwi TCMS supports email notifications which by default are sent over SMTP and
need to be configured via the following settings::

    EMAIL_HOST = ''
    EMAIL_PORT = 25
    EMAIL_FROM = 'kiwi@example.com'
    EMAIL_SUBJECT_PREFIX = '[Kiwi-TCMS] '

If you'd like to use an external email service, like Amazon SES you have to
configure the following settings instead::

    EMAIL_FROM = 'kiwi@example.com'
    EMAIL_BACKEND = 'django_ses.SESBackend'
    AWS_SES_ACCESS_KEY_ID = 'xxxxxxxxxxxxxxxxxxxx'
    AWS_SES_SECRET_ACCESS_KEY = 'YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY'

Also modify the Docker image to include the following lines::

    RUN pip install django_ses


Kerberos authentication
-----------------------

Kiwi TCMS supports passwordless authentication with Kerberos. This is
turned off by default because most organization do not use it. To enable
configure the following settings::

    MIDDLEWARE_CLASSES += (
        'django.contrib.auth.middleware.RemoteUserMiddleware',
    )

    AUTHENTICATION_BACKENDS += (
        'tcms.core.contrib.auth.backends.ModAuthKerbBackend',
    )

    KRB5_REALM='YOUR-DOMAIN.COM'


Also modify the Docker image to include the following lines::

    RUN yum -y install krb5-devel mod_auth_kerb
    RUN pip install kerberos
    COPY ./auth_kerb.conf /etc/httpd/conf.d/

Where ``auth_kerb.conf`` is your Kerberos configuration file for Apache!
More information about it can be found
`here <https://access.redhat.com/documentation/en-US/Red_Hat_JBoss_Web_Server/2/html/HTTP_Connectors_Load_Balancing_Guide/ch10s02s03.html>`_.

.. warning::

    Unless Kerberos authentication is configured and fully-operational the
    XML-RPC method `Auth.login_krbv()` will not work!
