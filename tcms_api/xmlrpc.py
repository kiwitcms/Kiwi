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

from http.client import HTTPSConnection
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
        For fixing https://bugzilla.redhat.com/show_bug.cgi?id=735937

        Return an individual HTTPS connection for each request.
        """
        chost, self._extra_headers, x509 = self.get_host_info(host)
        # Kiwi TCMS isn't ready to use HTTP/1.1 persistent connection mechanism.
        # So tell server current opened HTTP connection should be closed after
        # request is handled. And there will be a new connection for next request.
        self._extra_headers.append(('Connection', 'close'))
        self._connection = host, HTTPSConnection(  # nosec:B309:blacklist
            chost,
            None,
            **(x509 or {})
        )
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
