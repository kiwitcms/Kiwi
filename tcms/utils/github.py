# Copyright (c) 2019-2024 Alexander Todorov <atodorov@MrSenko.com>

import hashlib
import hmac

from django.http import HttpResponseForbidden


def calculate_signature(secret, contents):
    """
    Calculate GitHub signature header.

    WARNING: both parameters must be bytes, not string!
    """
    return "sha1=" + hmac.new(secret, msg=contents, digestmod=hashlib.sha1).hexdigest()


def verify_signature(request, secret):
    """
    Verifies request comes from GitHub, see:
    https://developer.github.com/webhooks/securing/
    """
    signature = request.headers.get("X-Hub-Signature", None)
    if not signature:
        return HttpResponseForbidden()

    expected = calculate_signature(secret, request.body)

    # due to security reasons do not use '==' operator
    # https://docs.python.org/3/library/hmac.html#hmac.compare_digest
    if not hmac.compare_digest(signature, expected):
        return HttpResponseForbidden()

    return True  # b/c of inconsistent-return-statements


def repo_id(url):
    """
    Return an owner/repository combo given a URL
    """
    result = url.strip().strip("/").lower()
    result = (
        result.replace("https://", "").replace("http://", "").replace("github.com/", "")
    )
    return result
