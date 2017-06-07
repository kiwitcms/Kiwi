KiwiTestPad configuration settings
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


Kerberos authentication
-----------------------

KiwiTestPad supports passwordless authentication with Kerberos. This is
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
