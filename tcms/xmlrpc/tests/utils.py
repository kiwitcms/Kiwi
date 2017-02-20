# -*- coding: utf-8 -*-

from xmlrpclib import Fault

from django import test
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission


class AssertMessage(object):
    NOT_VALIDATE_ARGS = "Missing validations for args."
    NOT_VALIDATE_REQUIRED_ARGS = "Missing validations for required args."
    NOT_VALIDATE_ILLEGAL_ARGS = "Missing validations for illegal args."
    NOT_VALIDATE_FOREIGN_KEY = "Missing validations for foreign key."
    NOT_VALIDATE_LENGTH = "Missing validations for length of value."
    NOT_VALIDATE_URL_FORMAT = "Missing validations for URL format."

    SHOULD_BE_1 = "Error code should be 1."
    SHOULD_BE_400 = "Error code should be 400."
    SHOULD_BE_401 = "Error code should be 401."
    SHOULD_BE_403 = "Error code should be 403."
    SHOULD_BE_404 = "Error code should be 404."
    SHOULD_BE_409 = "Error code should be 409."
    SHOULD_BE_500 = "Error code should be 500."
    SHOULD_BE_501 = "Error code should be 501."

    UNEXCEPT_ERROR = "Unexcept error occurs."
    NEED_ENCODE_UTF8 = "Need to encode with utf8."

    NOT_IMPLEMENT_FUNC = "Not implement yet."
    XMLRPC_INTERNAL_ERROR = "xmlrpc library error."
    NOT_VALIDATE_PERMS = "Missing validations for user perms."
    SHOULD_RAISE_EXCEPTION = "Should raise an exception."


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


def user_should_have_perm(user, perm):
    if isinstance(perm, basestring):
        try:
            app_label, codename = perm.split('.')
        except ValueError:
            raise ValueError('%s is not valid. Should be in format app_label.perm_codename')
        else:
            if not app_label or not codename:
                raise ValueError('Invalid app_label or codename')
            get_permission = Permission.objects.get
            user.user_permissions.add(
                get_permission(content_type__app_label=app_label, codename=codename))
    elif isinstance(perm, Permission):
        user.user_permissions.add(perm)
    else:
        raise TypeError('perm should be an instance of either basestring or Permission')


def remove_perm_from_user(user, perm):
    '''Remove a permission from an user'''
    if isinstance(perm, basestring):
        try:
            app_label, codename = perm.split('.')
        except ValueError:
            raise ValueError('%s is not valid. Should be in format app_label.perm_codename')
        else:
            if not app_label or not codename:
                raise ValueError('Invalid app_label or codename')
            get_permission = Permission.objects.get
            user.user_permissions.remove(
                get_permission(content_type__app_label=app_label, codename=codename))
    elif isinstance(perm, Permission):
        user.user_permissions.remove(perm)
    else:
        raise TypeError('perm should be an instance of either basestring or Permission')


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
    '''Factory method to make instance of FakeHTTPRequest'''
    _user = user
    if _user is None:
        _user = create_http_user()

    if user_perm is not None:
        user_should_have_perm(_user, user_perm)

    return FakeHTTPRequest(_user, data)
