# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django.urls import reverse_lazy

# Follows the format of ``tcms.settings.common.MENU_ITEMS``
MENU_ITEMS = [
    ("Fake Telemetry plugin", reverse_lazy("a_fake_plugin-example_view")),
    (
        "Fake Plugin sub-menu",
        [
            ("Example", reverse_lazy("a_fake_plugin-example_view")),
            ("-", "-"),
            (
                "3rd level menu",
                [
                    ("Go to Dashboard", "/"),
                    ("Go to kiwitcms.org", "http://kiwitcms.org"),
                ],
            ),
        ],
    ),
]
