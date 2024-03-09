# Copyright (c) 2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

"""
    Send a custom pageview event to Plausible.io so that we can count
    how many/which versions of Kiwi TCMS are out there in the wild!

    WARNING: this file is meant to be executed as a wsgi cron job,
    see etc/wsgi.conf for more details.
"""
import sys

import requests
from django.conf import settings


def post_analytics():
    response = requests.post(
        "https://plausible.io/api/event",
        json={
            "name": "pageview",
            "url": f"app://{settings.PLAUSIBLE_DOMAIN}/deployed-versions",
            "domain": settings.PLAUSIBLE_DOMAIN,
            "props": {
                "version": settings.KIWI_VERSION,
            },
        },
        headers={
            "User-Agent": f"kiwi-tcms/{settings.KIWI_VERSION}",
            "Content-Type": "application/json",
        },
        timeout=10,
    )

    print(response.status_code)
    print(response.headers)
    print(response.text)


if not settings.ANONYMOUS_ANALYTICS:
    print("Anonymous analytics are explicitly disabled. Exiting")
elif "manage.py" in sys.argv[0] and "shell" in sys.argv:
    # execute only when piped to `./manage.py shell`
    post_analytics()
else:
    print(
        "WARNING: pipe the content of this file to ./manage.py shell in order to execute it"
    )
