# Copyright (c) 2020 Alexander Todorov <atodorov@MrSenko.com>

from django.conf import settings
from django.contrib.auth.backends import BaseBackend


class AnonymousViewBackend(BaseBackend):
    """
    Backend which always returns True for *.view_* permissions for
    anonymous users! Add it to ``AUTHENTICATION_BACKENDS`` setting
    to enable read-only access which doesn't require login!
    """

    def has_perm(self, user_obj, perm, obj=None):
        if perm.find(".view_") > -1 and (
            user_obj.is_anonymous or user_obj.username == settings.ANONYMOUS_USER_NAME
        ):
            return True

        return super().has_perm(user_obj, perm, obj=obj)
