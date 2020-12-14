# pylint: disable=wildcard-import, unused-wildcard-import

"""
    Django settings for product env.
"""

import os

from tcms.settings.common import *  # noqa: F401,F403
from tcms.utils.settings import import_local_settings

# Debug settings
DEBUG = False


try:
    from .local_settings import *  # noqa: F401,F403
except ImportError:
    pass

try:
    import tcms_settings_dir

    import_local_settings(os.path.dirname(tcms_settings_dir.__file__))
except ImportError:
    pass
