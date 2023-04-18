# -*- coding: utf-8 -*-
#  pylint: disable=too-few-public-methods

import sys


def request_host_link(request, domain_name=None):
    protocol = "https://"
    if "runserver" in sys.argv:
        protocol = "http://"

    if request:
        if not domain_name:
            domain_name = request.get_host()
        # default to https if in production and we don't know
        protocol = "https://"
        if not request.is_secure():
            protocol = "http://"

    return protocol + domain_name
