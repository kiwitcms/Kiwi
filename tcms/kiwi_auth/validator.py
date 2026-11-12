# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under the GPL 2.0 or later: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django.contrib.auth import password_validation


class CommonPasswordValidator(password_validation.CommonPasswordValidator):
    def __init__(self, extra_passwords=(), **kwargs):
        super().__init__(**kwargs)
        for p in extra_passwords:
            # .strip().lower() matches what validate_password() does internally
            self.passwords.add(p.strip().lower())
