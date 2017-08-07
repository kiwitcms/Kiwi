from django.utils.deprecation import MiddlewareMixin
from pagination.middleware import PaginationMiddleware


class MyPaginationMiddleware(MiddlewareMixin, PaginationMiddleware):
    """
        New-style middleware for Django 1.10 until we drop
        django-pagination
    """
    pass


class CsrfDisableMiddleware(MiddlewareMixin):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        setattr(request, '_dont_enforce_csrf_checks', True)
