# -*- coding: utf-8 -*-
import xmlrpclib
import kerberos

from django.conf import settings


from django.core.validators import validate_email
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend, RemoteUserBackend

# from tcms
from tcms.core.contrib.auth import initiate_user_with_default_setups


class DBModelBackend(ModelBackend):
    can_login = True
    can_register = True
    can_logout = True


class EmailBackend(ModelBackend):
    # The source code is based on: http://www.djangosnippets.org/snippets/74/
    # All rights reserved by the orignal authors.
    """
    Email authorization backend for TCMS.
    """
    # Web UI Needed
    can_login = True
    can_register = True
    can_logout = True

    def authenticate(self, username=None, password=None):
        try:
            # If username is an email address, then try to pull it up
            validate_email(username)
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None
        except ValidationError:
            # We have a non-email address username we should try username
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None
        if user.check_password(password):
            return user


class BugzillaBackend(ModelBackend):
    """
    Bugzilla authorization backend for TCMS.

    It's required bugzilla xmlrpc.
    """
    # Web UI Needed
    can_login = True
    can_register = False
    can_logout = True

    # Disable for python 2.4 compatible
    # def __init__(self):
    # super(KerberosBackend, self).__init__()
    #    for var in ('BUGZILLA3_RPC_SERVER', ):
    #        if not hasattr(settings, var):
    #            raise ImproperlyConfigured(
    #                "Variable '%s' not set in settings." % var
    #            )

    def authenticate(self, username=None, password=None):
        server = xmlrpclib.ServerProxy(settings.BUGZILLA3_RPC_SERVER)

        try:
            validate_email(username)
            try:
                server.bugzilla.login(username, password)
            except xmlrpclib.Fault:
                return None

            try:
                user = User.objects.get(email=username)
                user.set_password(password)
                user.save()
            except User.DoesNotExist:
                user = User.objects.create_user(
                    username=username.split('@')[0],
                    email=username
                )

                user.set_unusable_password(password)
        except ValidationError:
            return None

        if user.check_password(password):
            return user


class KerberosBackend(ModelBackend):
    """
    Kerberos authorization backend for TCMS.

    Required python-kerberos backend, correct /etc/krb5.conf file,
    And correct KRB5_REALM settings in settings.py.

    Example in settings.py:
    # Kerberos settings
    KRB5_REALM = 'REDHAT.COM'
    """
    # Web UI Needed
    can_login = True
    can_register = False
    can_logout = True

    # Disable for python 2.4 compatible
    # def __init__(self):
    # super(KerberosBackend, self).__init__()
    #    for var in ('KRB5_REALM', ):
    #        if not hasattr(settings, var):
    #            raise ImproperlyConfigured(
    #                "Variable '%s' not set in settings." % var
    #            )

    def authenticate(self, username=None, password=None):
        try:
            kerberos.checkPassword(
                username, password, '',
                settings.KRB5_REALM
            )
        except kerberos.BasicAuthError:
            return None

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email='%s@%s' % (username, settings.KRB5_REALM.lower())
            )
        user.set_unusable_password()
        user.save()
        return user


class ModAuthKerbBackend(RemoteUserBackend):
    """
    mod_auth_kerb modules authorization backend for TCMS.
    Based on DjangoRemoteUser backend.

    Required correct /etc/krb5.conf, /etc/krb5.keytab and
    Correct mod_auth_krb5 module settings for apache.

    Example apache settings:

    # Set a httpd config to protect krb5login page with kerberos.
    # You need to have mod_auth_kerb installed to use kerberos auth.
    # Httpd config /etc/httpd/conf.d/<project>.conf should look like this:

    <Location "/">
        SetHandler python-program
        PythonHandler django.core.handlers.modpython
        SetEnv DJANGO_SETTINGS_MODULE <project>.settings
        PythonDebug On
    </Location>

    <Location "/auth/krb5login">
        AuthType Kerberos
        AuthName "<project> Kerberos Authentication"
        KrbMethodNegotiate on
        KrbMethodK5Passwd off
        KrbServiceName HTTP
        KrbAuthRealms EXAMPLE.COM
        Krb5Keytab /etc/httpd/conf/http.<hostname>.keytab
        KrbSaveCredentials off
        Require valid-user
    </Location>
    """
    # Web UI Needed
    can_login = False
    can_register = False
    can_logout = False

    # Disable for python 2.4 compatible
    # def __init__(self):
    # super(KerberosBackend, self).__init__()
    #    for var in ('KRB5_REALM', ):
    #        if not hasattr(settings, var):
    #            raise ImproperlyConfigured(
    #                "Variable '%s' not set in settings." % var
    #            )

    def configure_user(self, user):
        """
        Configures a user after creation and returns the updated user.

        By default, returns the user unmodified.
        """
        user.email = user.username + '@' + settings.KRB5_REALM.lower()
        user.set_unusable_password()
        user.save()
        initiate_user_with_default_setups(user)
        return user

    def clean_username(self, username):
        """
        Performs any cleaning on the "username" prior to using it to get or
        create the user object.  Returns the cleaned username.

        For more info, reference clean_username function in
        django/auth/backends.py
        """
        username = username.replace('@' + settings.KRB5_REALM, '')
        username_tuple = username.split('/')
        if len(username_tuple) > 1:
            username = username_tuple[1]
        return len(username) > 30 and username[:30] or username
