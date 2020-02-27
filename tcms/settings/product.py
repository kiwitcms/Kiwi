# pylint: disable=wildcard-import, unused-wildcard-import

"""
    Django settings for product env.
"""

from .common import *  # noqa: F401,F403

from tcms.utils.settings import import_local_settings


# Debug settings
DEBUG = False


try:
    from .local_settings import *  # noqa: F401,F403
except ImportError:
    pass


import_local_settings('local_settings_dir')
