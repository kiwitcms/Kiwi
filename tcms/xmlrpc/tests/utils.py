# -*- coding: utf-8 -*-

from six.moves.xmlrpc_client import Fault

from django import test
from django.contrib.auth.models import User

from tcms.tests import user_should_have_perm


class XmlrpcAPIBaseTest(test.TestCase):

    def assertRaisesXmlrpcFault(self, faultCode, method, *args, **kwargs):
        assert callable(method)
        try:
            method(*args, **kwargs)
        except Fault as f:
            self.assertEqual(f.faultCode, faultCode,
                             'Except raising fault error with code {0}, but {1} is raised'.format(
                                 faultCode, f.faultCode))
        except Exception as e:
            self.fail('Expect raising xmlrpclib.Fault, but {0} is raised and '
                      'message is "{1}".'.format(e.__class__.__name__, str(e)))
        else:
            self.fail('Expect to raise Fault error with faultCode {0}, '
                      'but no exception is raised.'.format(faultCode))


class FakeHTTPRequest(object):

    def __init__(self, user, data=None):
        self.user = user
        self.META = {}


def create_http_user():
    user, _ = User.objects.get_or_create(username='http_user',
                                         email='http_user@example.com')
    user.set_password(user.username)
    user.save()
    return user


def make_http_request(user=None, user_perm=None, data=None):
    """Factory method to make instance of FakeHTTPRequest"""
    _user = user
    if _user is None:
        _user = create_http_user()

    if user_perm is not None:
        user_should_have_perm(_user, user_perm)

    return FakeHTTPRequest(_user, data)
