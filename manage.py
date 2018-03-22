#!/usr/bin/env python
# pylint: disable=missing-docstring

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tcms.settings.devel")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
