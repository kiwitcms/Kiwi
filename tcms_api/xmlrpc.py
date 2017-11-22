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
url = https://tcms.example.com/xmlrpc/
use_mod_kerb = False

Or, more directly:

t = TCMSXmlrpc(
    'myusername',
    'foobar',
    'https://tcms.example.com/xmlrpc/',
)
t.testplan_get(10)
"""

from __future__ import print_function

import sys
from datetime import datetime, time

if sys.version_info.major == 2:
    import xmlrpclib
    import urllib2
    import httplib
    from cookielib import CookieJar
    from ConfigParser import SafeConfigParser as ConfigParser
else:
    import xmlrpc.client as xmlrpclib
    import urllib.request as urllib2
    import http.client as httplib
    from http.cookiejar import CookieJar
    from configparser import ConfigParser

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


class CookieTransport(xmlrpclib.Transport):
    '''A subclass of xmlrpclib.Transport that supports cookies.'''
    cookiejar = None
    scheme = 'http'

    def __init__(self):
        super(CookieTransport, self).__init__()
        self._cookies = []

    def send_headers(self, connection, headers):
        """
            Cookie handling on Python 3!
        """
        if self._cookies and sys.version_info >= (3,):
            connection.putheader("Cookie", "; ".join(self._cookies))
        super(CookieTransport, self).send_headers(connection, headers)

    def parse_response(self, response):
        """
            Cookie handling on Python 3!
        """
        if sys.version_info >= (3,):
            for header in response.msg.get_all("Set-Cookie", []):
                cookie = header.split(";", 1)[0]
                self._cookies.append(cookie)
        return super(CookieTransport, self).parse_response(response)

    # Cribbed from xmlrpclib.Transport.send_user_agent
    def send_cookies(self, connection, cookie_request):
        """
            NOTE: Only used on Python 2!
        """
        if sys.version_info >= (3,):
            return

        if self.cookiejar is None:
            self.cookiejar = CookieJar()
        elif self.cookiejar:
            # Let the cookiejar figure out what cookies are appropriate
            self.cookiejar.add_cookie_header(cookie_request)
            # Pull the cookie headers out of the request object...
            cookielist = list()
            for h, v in cookie_request.header_items():
                if h.startswith('Cookie'):
                    cookielist.append([h, v])
            # ...and put them over the connection
            for h, v in cookielist:
                connection.putheader(h, v)

    def request_with_cookies(self, host, handler, request_body, verbose=0):
        """
            NOTE: Only used on Python 2.6 and earlier!

            This is the same request() method from xmlrpclib.Transport,
            with a couple additions noted below
        """
        if sys.version_info >= (3,):
            return

        h = self.make_connection(host)
        if verbose:
            h.set_debuglevel(1)

        # ADDED: construct the URL and Request object for proper cookie handling
        request_url = "%s://%s%s" % (self.scheme, host, handler)
        # log.debug("request_url is %s" % request_url)
        cookie_request = urllib2.Request(request_url)

        self.send_request(h, handler, request_body)
        self.send_host(h, host)
        # ADDED. creates cookiejar if None.
        self.send_cookies(h, cookie_request)
        self.send_user_agent(h)
        self.send_content(h, request_body)

        errcode, errmsg, headers = h.getreply()

        # ADDED: parse headers and get cookies here
        cookie_response = CookieResponse(headers)
        # Okay, extract the cookies from the headers
        self.cookiejar.extract_cookies(cookie_response, cookie_request)
        # log.debug("cookiejar now contains: %s" % self.cookiejar._cookies)
        # And write back any changes
        if hasattr(self.cookiejar, 'save'):
            try:
                self.cookiejar.save(self.cookiejar.filename)
            except Exception as e:
                raise
                # log.error("Couldn't write cookiefile %s: %s" % \
                #        (self.cookiejar.filename,str(e)))

        if errcode != 200:
            # When runs here, the HTTPS connection isn't useful any more
            #   before raising an exception to caller
            h.close()

            raise xmlrpclib.ProtocolError(
                host + handler,
                errcode, errmsg,
                headers
            )

        self.verbose = verbose

        try:
            sock = h._conn.sock
        except AttributeError:
            sock = None

        try:
            return self._parse_response(h.getfile(), sock)
        finally:
            h.close()

    def single_request_with_cookies(self, host, handler, request_body, verbose=0):
        """
            NOTE: Only used on Python 2.7!

            This is just python 2.7's xmlrpclib.Transport.single_request, with
            send additions noted below to send cookies along with the request
        """
        if sys.version_info >= (3,):
            return

        h = self.make_connection(host)
        if verbose:
            h.set_debuglevel(1)

        # ADDED: construct the URL and Request object for proper cookie handling
        request_url = "%s://%s%s" % (self.scheme, host, handler)
        # log.debug("request_url is %s" % request_url)
        cookie_request = urllib2.Request(request_url)

        try:
            self.send_request(h, handler, request_body)
            self.send_host(h, host)
            # ADDED. creates cookiejar if None.
            self.send_cookies(h, cookie_request)
            self.send_user_agent(h)
            self.send_content(h, request_body)

            response = h.getresponse(buffering=True)

            # ADDED: parse headers and get cookies here
            cookie_response = CookieResponse(response.msg)
            # Okay, extract the cookies from the headers
            self.cookiejar.extract_cookies(cookie_response, cookie_request)
            # log.debug("cookiejar now contains: %s" % self.cookiejar._cookies)
            # And write back any changes
            if hasattr(self.cookiejar, 'save'):
                try:
                    self.cookiejar.save(self.cookiejar.filename)
                except Exception as e:
                    raise
                    # log.error("Couldn't write cookiefile %s: %s" % \
                    #        (self.cookiejar.filename,str(e)))

            if response.status == 200:
                self.verbose = verbose
                return self.parse_response(response)

            if (response.getheader("content-length", 0)):
                response.read()
            raise xmlrpclib.ProtocolError(
                host + handler,
                response.status, response.reason,
                response.msg,
            )
        except xmlrpclib.Fault:
            raise
        finally:
            h.close()

    # Override the appropriate request method
    if sys.version_info.major >= 3:
        pass
    elif hasattr(xmlrpclib.Transport, 'single_request'):
        single_request = single_request_with_cookies  # python 2.7+
    else:
        request = request_with_cookies  # python 2.6 and earlier


class SafeCookieTransport(xmlrpclib.SafeTransport, CookieTransport):
    '''SafeTransport subclass that supports cookies.'''
    scheme = 'https'
    # Override the appropriate request method
    if sys.version_info.major >= 3:
        pass
    elif hasattr(xmlrpclib.Transport, 'single_request'):
        single_request = CookieTransport.single_request_with_cookies
    else:
        request = CookieTransport.request_with_cookies

# Stolen from FreeIPA source freeipa-1.2.1/ipa-python/krbtransport.py


class KerbTransport(SafeCookieTransport):
    """Handles Kerberos Negotiation authentication to an XML-RPC server."""

    def get_host_info(self, host):
        import kerberos

        host, extra_headers, x509 = xmlrpclib.Transport.get_host_info(
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

    def _python_ver_larger_than_2_6(self):
        return sys.version_info >= (2, 6)

    def make_connection(self, host):
        '''
        For fixing bug #735937.
        When running on Python 2.7, make_connection will do the same behavior as that of
        Python 2.6's xmlrpclib. That is in Python 2.6, make_connection will return an
        individual HTTPS connection for each request
        '''

        if self._python_ver_larger_than_2_6():
            # create a HTTPS connection object from a host descriptor
            # host may be a string, or a (host, x509-dict) tuple
            try:
                HTTPS = httplib.HTTPSConnection
            except AttributeError:
                raise NotImplementedError(
                    "your version of httplib doesn't support HTTPS"
                )
            else:
                chost, self._extra_headers, x509 = self.get_host_info(host)
                # Kiwi TCMS isn't ready to use HTTP/1.1 persistent connection mechanism.
                # So tell server current opened HTTP connection should be closed after
                # request is handled. And there will be a new connection for next request.
                self._extra_headers.append(('Connection', 'close'))
                self._connection = host, HTTPS(chost, None, **(x509 or {}))
                return self._connection[1]

        else:
            # For Python 2.6, do the default behavior
            return SafeCookieTransport.make_connection(self, host)


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
        self.server = xmlrpclib.ServerProxy(
            url,
            transport=self._transport,
            verbose=VERBOSE,
            allow_none=1
        )

        # Login, get a cookie into our cookie jar (login_dict):
        self.do_command("Auth.login", [dict(
            username=username,
            password=password,
        )])

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

    def do_command(self, verb, args=[]):
        """Submit a command to the server proxy.

        'verb' -- string, the xmlrpc verb,
        'args' -- list, the argument list,
        """
        params = ''
        for arg in args:
            params = ("%s" % str(arg), "%s, %s" %
                      (params, str(arg)))[params != '']
        cmd = "self.server." + verb + "(" + params + ")"
        if DEBUG:
            print(cmd)

        try:
            return eval(cmd)
        except xmlrpclib.Error as e:
            raise TCMSXmlrpcError(verb, params, e)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Build ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def build_get(self, build_id):
        """Get A Build by ID.

        'build_id' -- integer, Must be greater than 0

        Example: build_get(10)

        Result: A dictionary of key/value pairs for the attributes listed above
        """
        return self.do_command("Build.get", [self._number_noop(build_id)])

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ User ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def get_me(self):
        """
        Description: Get the information of myself

        Returns:     A blessed User object Hash
        """
        return self.do_command("User.get_me")


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
        self.server = xmlrpclib.ServerProxy(
            url,
            transport=self._transport,
            verbose=VERBOSE,
            allow_none=1
        )

        # Login, get a cookie into our cookie jar (login_dict):
        self.do_command("Auth.login_krbv", [])
