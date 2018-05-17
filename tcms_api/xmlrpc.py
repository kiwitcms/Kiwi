"""
XMLRPC driver

Use this class to access Kiwi TCMS via XML-RPC
This code is based on
http://landfill.bugzilla.org/testopia2/testopia/contrib/drivers/python/testopia.py
and https://fedorahosted.org/python-bugzilla/browser/bugzilla/base.py

History:
2011-12-31 bugfix https://bugzilla.redhat.com/show_bug.cgi?id=735937

Example on how to access this library,

from tcms_api import TCMSXmlrpc

n = TCMSXmlrpc.from_config('config.cfg')
n.testplan_get(10)

where config.cfg looks like:
[tcms]
username = myusername
password = foobar
url = https://tcms.example.com/xml-rpc/
use_mod_kerb = False

Or, more directly:

t = TCMSXmlrpc(
    'myusername',
    'foobar',
    'https://tcms.example.com/xml-rpc/',
)
t.testplan_get(10)
"""

import errno
import http.client
import xmlrpc.client
from configparser import ConfigParser
from datetime import datetime, time
from http.cookiejar import CookieJar

VERBOSE = 0
DEBUG = 0


class CookieResponse:
    '''Fake HTTPResponse object that we can fill with headers we got elsewhere.
    We can then pass it to CookieJar.extract_cookies() to make it pull out the
    cookies from the set of headers we have.'''

    def __init__(self, headers):
        self.headers = headers
        # log.debug("CookieResponse() headers = %s" % headers)

    def info(self):
        return self.headers


class CookieTransport(xmlrpc.client.Transport):
    '''A subclass of xmlrpc.client.Transport that supports cookies.'''
    cookiejar = None
    scheme = 'http'

    def __init__(self, use_datetime=False, use_builtin_types=False):
        super(CookieTransport, self).__init__(use_datetime=use_datetime,
                                              use_builtin_types=use_builtin_types)
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
            except OSError as e:
                if i or e.errno not in (errno.ECONNRESET, errno.ECONNABORTED,
                                        errno.EPIPE):
                    raise

    def send_headers(self, connection, headers):
        if self._cookies:
            connection.putheader("Cookie", "; ".join(self._cookies))
        super(CookieTransport, self).send_headers(connection, headers)

    def parse_response(self, response):
        for header in response.msg.get_all("Set-Cookie", []):
            cookie = header.split(";", 1)[0]
            self._cookies.append(cookie)
        return super(CookieTransport, self).parse_response(response)


class SafeCookieTransport(xmlrpc.client.SafeTransport, CookieTransport):
    '''SafeTransport subclass that supports cookies.'''
    scheme = 'https'


# Stolen from FreeIPA source freeipa-1.2.1/ipa-python/krbtransport.py
class KerbTransport(SafeCookieTransport):
    """Handles Kerberos Negotiation authentication to an XML-RPC server."""

    def get_host_info(self, host):
        import kerberos

        host, extra_headers, x509 = xmlrpc.client.Transport.get_host_info(
            self, host)

        # Set the remote host principal
        h = host
        hostinfo = h.split(':')
        service = "HTTP@" + hostinfo[0]

        rc, vc = kerberos.authGSSClientInit(service)
        kerberos.authGSSClientStep(vc, "")

        extra_headers = [
            ("Authorization", "negotiate %s" %
             kerberos.authGSSClientResponse(vc))
        ]

        return host, extra_headers, x509

    def make_connection(self, host):
        '''
        For fixing bug #735937.
        When running on Python 2.7, make_connection will do the same behavior as that of
        Python 2.6's xmlrpc.client. That is in Python 2.6, make_connection will return an
        individual HTTPS connection for each request
        '''

        # create a HTTPS connection object from a host descriptor
        # host may be a string, or a (host, x509-dict) tuple
        try:
            HTTPS = http.client.HTTPSConnection
        except AttributeError:
            raise NotImplementedError(
                "your version of http.client doesn't support HTTPS"
            )
        else:
            chost, self._extra_headers, x509 = self.get_host_info(host)
            # Kiwi TCMS isn't ready to use HTTP/1.1 persistent connection mechanism.
            # So tell server current opened HTTP connection should be closed after
            # request is handled. And there will be a new connection for next request.
            self._extra_headers.append(('Connection', 'close'))
            self._connection = host, HTTPS(chost, None, **(x509 or {}))
            return self._connection[1]


class TCMSError(Exception):
    pass


class TCMSXmlrpcError(Exception):
    def __init__(self, verb, params, wrappedError):
        self.verb = verb
        self.params = params
        self.wrappedError = wrappedError

    def __str__(self):
        return "Error while executing cmd '%s' --> %s" \
               % (self.verb + "(" + self.params + ")", self.wrappedError)


class TCMSXmlrpc(object):
    """
    TCMSXmlrpc - TCMS XML-RPC client
                    for server deployed without BASIC authentication
    """

    @classmethod
    def from_config(cls, filename):
        cp = ConfigParser()
        cp.read([filename])
        kwargs = dict(
            [(key, cp.get('tcms', key)) for key in [
                'username', 'password', 'url'
            ]]
        )

        return TCMSXmlrpc(**kwargs)

    def __init__(self, username, password, url, use_mod_auth_kerb=False):
        if url.startswith('https://'):
            self._transport = SafeCookieTransport()
        elif url.startswith('http://'):
            self._transport = CookieTransport()
        else:
            raise TCMSError("Unrecognized URL scheme")

        self._transport.cookiejar = CookieJar()
        # print("COOKIES:", self._transport.cookiejar._cookies)
        self.server = xmlrpc.client.ServerProxy(
            url,
            transport=self._transport,
            verbose=VERBOSE,
            allow_none=1
        )

        # Login, get a cookie into our cookie jar (login_dict):
        self.server.Auth.login(username, password)

        # Record the user ID in case the script wants this
        # self.user_id = login_dict['id']
        # print('Logged in with cookie for user %i' % self.userId)
        # print("COOKIES:", self._transport.cookiejar._cookies)

    def _boolean_option(self, option, value):
        """Returns the boolean option when value is True or False, else ''

        Example: _boolean_option('isactive', True) returns " 'isactive': 1,"
        """
        if value or str(value) == 'False':
            if not isinstance(value, bool):
                raise TCMSError(
                    "The value for the option '%s' is not boolean." % option)
            elif value is False:
                return "\'%s\':0, " % option
            elif value is True:
                return "\'%s\':1, " % option
        return ''

    def _datetime_option(self, option, value):
        """Returns the string 'option': 'value' where value is a date object formatted
        in string as yyyy-mm-dd hh:mm:ss. If value is None, then we return ''.

        Example: self._time_option('datetime', datetime(2007,12,05,13,01,03))
        returns "'datetime': '2007-12-05 13:01:03'"
        """
        if value:
            if not isinstance(value, datetime):
                raise TCMSError(
                    "The option '%s' is not a valid datetime object." % option)
            return "\'%s\':\'%s\', " % (option, value.strftime("%Y-%m-%d %H:%M:%S"))
        return ''

    def _list_dictionary_option(self, option, value):
        """Verifies that the value passed for the option is in the format of a list
        of dictionaries.

        Example: _list_dictionary_option('plan':[{'key1': 'value1', 'key2': 'value2'}])
        verifies that value is a list, then verifies that the content of value are dictionaries.
        """
        if value:  # Verify that value is a type of list
            if not isinstance(value, list):
                raise TCMSError(
                    "The option '%s' is not a valid list of dictionaries." % option)
            else:
                # Verify that the content of value are dictionaries,
                for item in value:
                    if not isinstance(item, dict):
                        raise TCMSError(
                            "The option '%s' is not a valid list of dictionaries." % option)
            return "\'%s\': %s" % (option, value)
        return ''

    _list_dict_op = _list_dictionary_option

    def _number_option(self, option, value):
        """Returns the string " 'option': value," if value is not None, else ''

        Example: self._number_option("isactive", 1) returns " 'isactive': 1,"
        """
        if value:
            if not isinstance(value, int):
                raise TCMSError(
                    "The option '%s' is not a valid integer." % option)
            return "\'%s\':%d, " % (option, value)
        return ''

    def _number_no_option(self, number):
        """Returns the number in number. Just a totally useless wrapper :-)

        Example: self._number_no_option(1) returns 1
        """
        if not isinstance(number, int):
            raise TCMSError("The 'number' parameter is not an integer.")
        return str(number)

    _number_noop = _number_no_option

    def _options_dict(self, *args):
        """Creates a wrapper around all the options into a dictionary format.

        Example, if args is ['isactive': 1,", 'description', 'Voyage project'], then
        the return will be {'isactive': 1,", 'description', 'Voyage project'}
        """
        return "{%s}" % ''.join(args)

    def _options_non_empty_dict(self, *args):
        """Creates a wrapper around all the options into a dictionary format and
        verifies that the dictionary is not empty.

        Example, if args is ['isactive': 1,", 'description', 'Voyage project'], then
        the return will be {'isactive': 1,", 'description', 'Voyage project'}.
        If args is empty, then we raise an error.
        """
        if not args:
            raise TCMSError("At least one variable must be set.")
        return "{%s}" % ''.join(args)

    _options_ne_dict = _options_non_empty_dict

    def _string_option(self, option, value):
        """Returns the string 'option': 'value'. If value is None, then ''

        Example: self._string_option('description', 'Voyage project') returns
        "'description' : 'Voyage project',"
        """
        if value:
            if not isinstance(value, str):
                raise TCMSError(
                    "The option '%s' is not a valid string." % option)
            return "\'%s\':\'%s\', " % (option, value)
        return ''

    def _string_no_option(self, option):
        """Returns the string 'option'.

        Example: self._string_no_option("description") returns "'description'"
        """
        if option:
            if not isinstance(option, str):
                raise TCMSError(
                    "The option '%s' is not a valid string." % option)
            return "\'%s\'" % option
        return ''

    _string_noop = _string_no_option

    def _time_option(self, option, value):
        """Returns the string 'option': 'value' where value is a time object formatted in string
        as hh:mm:ss. If value is None, then we return ''.

        Example: self._time_option('time', time(12,00,03)) returns "'time': '12:00:03'"
        """
        if value:
            if not isinstance(value, time):
                raise TCMSError(
                    "The option '%s' is not a valid time object." % option)
            return "\'%s\':\'%s\', " % (option, value.strftime("%H:%M:%S"))
        return ''


class TCMSKerbXmlrpc(TCMSXmlrpc):
    """
    TCMSXmlrpc - TCMS XML-RPC client
                    for server deployed with mod_auth_kerb
    """

    def __init__(self, url):
        if url.startswith('https://'):
            self._transport = KerbTransport()
        elif url.startswith('http://'):
            raise TCMSError("Encrypted https communication required for "
                            "Kerberos authentication.\nURL provided: {0}".format(url))
        else:
            raise TCMSError("Unrecognized URL scheme: {0}".format(url))

        self._transport.cookiejar = CookieJar()
        # print("COOKIES:", self._transport.cookiejar._cookies)
        self.server = xmlrpc.client.ServerProxy(
            url,
            transport=self._transport,
            verbose=VERBOSE,
            allow_none=1
        )

        # Login, get a cookie into our cookie jar (login_dict):
        self.server.Auth.login_krbv()
