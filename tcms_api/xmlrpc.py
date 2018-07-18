"""
XMLRPC driver

Use this class to access Kiwi TCMS via XML-RPC
This code is based on
http://landfill.bugzilla.org/testopia2/testopia/contrib/drivers/python/testopia.py
and https://fedorahosted.org/python-bugzilla/browser/bugzilla/base.py

History:
2011-12-31 bugfix https://bugzilla.redhat.com/show_bug.cgi?id=735937
"""
# pylint: disable=too-few-public-methods

import errno
import http.client
from http.cookiejar import CookieJar
import xmlrpc.client

VERBOSE = 0


class CookieTransport(xmlrpc.client.Transport):
    """A subclass of xmlrpc.client.Transport that supports cookies."""
    cookiejar = None
    scheme = 'http'

    def __init__(self, use_datetime=False, use_builtin_types=False):
        super().__init__(use_datetime=use_datetime, use_builtin_types=use_builtin_types)
        self._cookies = []

    def request(self, host, handler, request_body, verbose=False):
        # retry request once if cached connection has gone cold
        for i in (0, 1):
            try:
                return self.single_request(host, handler, request_body, verbose)
            # the order of these except blocks is reversed in Python 3.5 which
            # leads to errors, partially due to Django's 2.0 disabling of
            # keep-alive connections. See
            # https://code.djangoproject.com/ticket/28968
            # https://bugs.python.org/issue26402
            except http.client.RemoteDisconnected:
                if i:
                    raise
            except OSError as error:
                if i or error.errno not in (errno.ECONNRESET, errno.ECONNABORTED, errno.EPIPE):
                    raise

    def send_headers(self, connection, headers):
        if self._cookies:
            connection.putheader("Cookie", "; ".join(self._cookies))
        super().send_headers(connection, headers)

    def parse_response(self, response):
        for header in response.msg.get_all("Set-Cookie", []):
            cookie = header.split(";", 1)[0]
            self._cookies.append(cookie)
        return super().parse_response(response)


class SafeCookieTransport(xmlrpc.client.SafeTransport, CookieTransport):
    """SafeTransport subclass that supports cookies."""
    scheme = 'https'


# Taken from FreeIPA source freeipa-1.2.1/ipa-python/krbtransport.py
class KerbTransport(SafeCookieTransport):
    """Handles Kerberos Negotiation authentication to an XML-RPC server."""

    def get_host_info(self, host):
        import kerberos

        host, extra_headers, x509 = xmlrpc.client.Transport.get_host_info(self, host)

        # Set the remote host principal
        hostinfo = host.split(':')
        service = "HTTP@" + hostinfo[0]

        _result, context = kerberos.authGSSClientInit(service)
        kerberos.authGSSClientStep(context, "")

        extra_headers = [
            ("Authorization", "negotiate %s" %
             kerberos.authGSSClientResponse(context))
        ]

        return host, extra_headers, x509

    def make_connection(self, host):
        """
        For fixing bug #735937.
        When running on Python 2.7, make_connection will do the same behavior as that of
        Python 2.6's xmlrpc.client. That is in Python 2.6, make_connection will return an
        individual HTTPS connection for each request
        """

        # create a HTTPS connection object from a host descriptor
        # host may be a string, or a (host, x509-dict) tuple
        try:
            HTTPS = http.client.HTTPSConnection
        except AttributeError:
            raise NotImplementedError("your version of http.client doesn't support HTTPS")
        else:
            chost, self._extra_headers, x509 = self.get_host_info(host)
            # Kiwi TCMS isn't ready to use HTTP/1.1 persistent connection mechanism.
            # So tell server current opened HTTP connection should be closed after
            # request is handled. And there will be a new connection for next request.
            self._extra_headers.append(('Connection', 'close'))
            self._connection = host, HTTPS(chost, None, **(x509 or {}))
            return self._connection[1]


class TCMSXmlrpc:
    """
    TCMS XML-RPC client for server deployed without BASIC authentication.
    """
    def __init__(self, username, password, url):
        if url.startswith('https://'):
            self._transport = SafeCookieTransport()
        elif url.startswith('http://'):
            self._transport = CookieTransport()
        else:
            raise Exception("Unrecognized URL scheme")

        self._transport.cookiejar = CookieJar()
        self.server = xmlrpc.client.ServerProxy(
            url,
            transport=self._transport,
            verbose=VERBOSE,
            allow_none=1
        )

        # Login, get a cookie into our cookie jar (login_dict):
        self.server.Auth.login(username, password)


class TCMSKerbXmlrpc(TCMSXmlrpc):
    """
    TCMSXmlrpc - TCMS XML-RPC client
                    for server deployed with mod_auth_kerb
    """

    def __init__(self, url):  # pylint: disable=super-init-not-called
        if url.startswith('https://'):
            self._transport = KerbTransport()
        elif url.startswith('http://'):
            raise Exception("Encrypted https communication required for "
                            "Kerberos authentication.\nURL provided: {0}".format(url))
        else:
            raise Exception("Unrecognized URL scheme: {0}".format(url))

        self._transport.cookiejar = CookieJar()
        self.server = xmlrpc.client.ServerProxy(
            url,
            transport=self._transport,
            verbose=VERBOSE,
            allow_none=1
        )

        # Login, get a cookie into our cookie jar (login_dict):
        self.server.Auth.login_krbv()
