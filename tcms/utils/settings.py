# Copyright (c) 2020 Alexander Todorov <atodorov@MrSenko.com>

import os
import importlib

from django.conf import settings as django_settings

import tcms.settings


def local_settings_files(scan_dir):
    """
        Returns a sorted list of 1st level files found under
        @scan_dir, except __init__.py.

        These files will later be imported to override Django settings!

        WARNING: file names must be valid Python module names!!!
    """
    module_names = []
    for entry in os.scandir(scan_dir):
        if entry.is_file() and entry.name != '__init__.py':
            module_names.append(entry.name.replace('.py', ''))
    module_names.sort()

    return module_names


def import_local_settings(scan_dir):
    """
        Performs `from scan_dir.<module> import *` in alphabetic order for all files
        found under @scan_dir.

        @scan_dir is a directory(parent module) under tcms/settings/!
    """
    absolute_scan_dir = os.path.join(os.path.dirname(tcms.settings.__file__), scan_dir)
    for module_name in local_settings_files(absolute_scan_dir):
        import_name = "tcms.settings.%s.%s" % (scan_dir, module_name)
        module = importlib.import_module(import_name)

        # override anything which looks like a constant,
        # e.g. capital letters. This is exactly what Django does
        for setting_name in dir(module):
            if setting_name.isupper():
                setting_value = getattr(module, setting_name)
                setattr(django_settings, setting_name, setting_value)
