# -*- coding: utf-8 -*-
from tcms.integration.djqpid import settings as st


def refresh_HTTP_credential_cache():
    '''
    Put service ticket into credential cache from service's keytab file.

    Return the credential cache file name.
    '''

    import krbV
    import os

    keytab_file = st.SERVICE_KEYTAB
    principal_name = st.SERVICE_PRINCIPAL
    # This is the credential cache file, according to the Kerberbos V5 standard
    ccache_file = '/tmp/krb5cc_%d_%d' % (os.getuid(), os.getpid())

    ctx = krbV.default_context()
    princ = krbV.Principal(name=principal_name, context=ctx)
    if keytab_file:
        keytab = krbV.Keytab(name=keytab_file, context=ctx)
    else:
        # According the documentation of MIT Kerberos V5,
        # default keytab file is /etc/krb5.keytab. It might be changed
        # by modifying default_keytab_name in krb5.conf
        keytab = ctx.default_keytab()
    ccache = krbV.CCache(name=ccache_file, context=ctx)

    ccache.init(princ)
    ccache.init_creds_keytab(principal=princ, keytab=keytab)

    return ccache_file
