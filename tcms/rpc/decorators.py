from collections.abc import Callable

from django.http import HttpRequest


def django_login_required(request: HttpRequest):
    """
    API clients must call Auth.login which sets the Django session cookie.
    Which is then inspected/understood by existing middleware which
    sets request.user!
    """
    try:
        user = request.user
        if user.is_authenticated:
            return user
        return None
    except Exception:  # pylint: disable=broad-exception-caught
        return None


def permissions_required(*perms: str) -> Callable[[HttpRequest], object | None]:
    def check(request: HttpRequest):  # pylint: disable=nested-function-found
        user = django_login_required(request)
        if user and user.has_perms(perms):
            return user
        return None

    return check
