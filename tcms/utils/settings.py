# Copyright (c) 2020 Alexander Todorov <atodorov@MrSenko.com>

import glob
import inspect
import os


def import_local_settings(scan_dir, **kwargs):
    """
    Add/override the global settings object with additional settings
    defined in files found under @scan_dir.

    Files are executed in alphabetic order!

    @scan_dir is an absolute directory path!
    """
    # we are getting globals() from previous frame globals - it is caller's globals()
    scope = kwargs.pop("scope", inspect.stack()[1][0].f_globals)

    override_files = glob.glob(os.path.join(scan_dir, "*.py"))
    override_files.sort()
    for fname in override_files:
        if fname.endswith("__init__.py"):
            continue
        # Similar to what Transifex does
        # https://code.djangoproject.com/wiki/SplitSettings#Usingexectoincorporatelocalsettings
        # https://code.djangoproject.com/wiki/SplitSettings#UsingalistofconffilesTransifex
        exec(  # nosec:B102:exec_used pylint: disable=exec-used
            open(fname, "rb").read(), scope
        )
