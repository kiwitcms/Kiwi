# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.contrib.auth.models import Permission


def user_should_have_perm(user, perm):
    if isinstance(perm, basestring):
        try:
            app_label, codename = perm.split('.')
        except ValueError:
            raise ValueError('%s is not valid. Should be in format '
                             'app_label.perm_codename')
        else:
            if not app_label or not codename:
                raise ValueError('Invalid app_label or codename')
            get_permission = Permission.objects.get
            user.user_permissions.add(
                get_permission(content_type__app_label=app_label,
                               codename=codename))
    elif isinstance(perm, Permission):
        user.user_permissions.add(perm)
    else:
        raise TypeError(
            'perm should be an instance of either basestring or Permission')


def remove_perm_from_user(user, perm):
    '''Remove a permission from an user'''
    if isinstance(perm, basestring):
        try:
            app_label, codename = perm.split('.')
        except ValueError:
            raise ValueError('%s is not valid. Should be in format '
                             'app_label.perm_codename')
        else:
            if not app_label or not codename:
                raise ValueError('Invalid app_label or codename')
            get_permission = Permission.objects.get
            user.user_permissions.remove(
                get_permission(content_type__app_label=app_label,
                               codename=codename))
    elif isinstance(perm, Permission):
        user.user_permissions.remove(perm)
    else:
        raise TypeError(
            'perm should be an instance of either basestring or Permission')


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
