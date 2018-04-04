# pylint: disable=no-self-use, too-few-public-methods

from django.utils.deprecation import MiddlewareMixin


class CsrfDisableMiddleware(MiddlewareMixin):
    def process_view(self, request, _callback, _callback_args, _callback_kwargs):
        setattr(request, '_dont_enforce_csrf_checks', True)
