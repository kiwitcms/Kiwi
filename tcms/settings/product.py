# pylint: disable=wildcard-import, unused-wildcard-import

"""
    Django settings for product env.
"""

from .common import *  # noqa: F401,F403

# Debug settings
DEBUG = False

try:
    from .local_settings import *  # noqa: F401,F403
except ImportError:
    pass
