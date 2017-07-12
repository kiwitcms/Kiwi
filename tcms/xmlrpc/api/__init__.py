# -*- coding: utf-8 -*-

from auth import *  # NOQA
from build import *  # NOQA
from env import *  # NOQA
from product import *  # NOQA
from tag import *  # NOQA
from testcaserun import *  # NOQA
from testcase import *  # NOQA
from testcaseplan import *  # NOQA
from testrun import *  # NOQA
from user import *  # NOQA
from version import *  # NOQA

from tcms.xmlrpc.filters import autowrap_xmlrpc_apis
autowrap_xmlrpc_apis(__path__, __package__)  # NOQA
