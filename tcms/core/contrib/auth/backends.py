# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.auth.backends import ModelBackend, RemoteUserBackend

from tcms.utils.permissions import assign_default_group_permissions


class DBModelBackend(ModelBackend):
    can_login = True
    can_register = True
    can_logout = True


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

    def authenticate(self, request, username=None, password=None):
        import kerberos

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

    def configure_user(self, user):
        """
        Configures a user after creation and returns the updated user.

        By default, returns the user unmodified.
        """
        user.email = user.username + '@' + settings.KRB5_REALM.lower()
        user.set_unusable_password()
        user.is_active = True
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


def initiate_user_with_default_setups(user):
    '''
    Add default groups, permissions, status to a newly
    created user.
    '''
    # create default permissions if not already set
    assign_default_group_permissions()

    default_groups = Group.objects.filter(name__in=settings.DEFAULT_GROUPS)
    for grp in default_groups:
        user.groups.add(grp)

    user.is_staff = True  # so they can add Products, Builds, etc via the ADMIN menu
    user.save()
