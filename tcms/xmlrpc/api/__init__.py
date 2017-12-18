# -*- coding: utf-8 -*-

"""
Kiwi TCMS XML-RPC Service
-------------------------

You need to invoke it using an XML-RPC Client! For the available XML-RPC methods
checkout the **Submodules** section!

`tcms-api <https://pypi.org/project/tcms-api/>`_ is the official Python
interface for Kiwi TCMS! We strongly advise that you use it instead of
directly calling the XML-RPC methods below!


How does the XML-RPC interface work?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **[Model].filter** - the ``filter`` method is a full featured wrapper of Django
  QuerySet's ``.filter()`` method. It has the following features:

  - **Relationship** - for example to get all test cases belonging to 'RHEL 5' we
    we use the category path for recommend::

        >>> TestCase.filter({'category__product__name': 'Red Hat Enterprise Linux 5'})

  - **Field lookups** - for example to get all test cases with summary starting with
    'test'::

        >>> TestCase.filter({'summary__startswith': 'test'})

  Access
  `this URL <https://docs.djangoproject.com/en/dev/ref/models/querysets/#field-lookups>`_
  for more information.


- **[Model].filter_count** - provides the count of filtered results.


How to handle ForeignKey arguments?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to the basic types such as int, str and bool, there is a
relationship type called ForeignKey. The syntax of using ForeignKey in this
XMLRPC API is quite simple::

    foreignkey + '__' + fieldname + '__' + query_syntax

Taking ``TestCase.filter()`` for example, if the query is based on a
``default_tester``'s username which starts with 'John', the syntax will look
like this::

    TestCase.filter({'user__username__startswith': 'John'})

In this case the foreignkey is 'user', fieldname is 'username', and query_syntax
is 'startswith'. They are joined together using double underscores '__'. This is
the same syntax used by Django QuerySet!.

For all the XML-RPC methods we have listed the available ForeignKey, however
for the available ForeignKey field names that can be used in a query
please check out Kiwi TCMS's source code on
`GitHub <https://github.com/kiwitcms/Kiwi>`_. The definitions are located in
files named 'models.py'. For a detailed query syntax documentation, please
check-out the
`Django documentation <https://docs.djangoproject.com/en/dev/topics/db/queries/#field-lookups>`_.
"""

from .auth import *  # NOQA
from .build import *  # NOQA
from .env import *  # NOQA
from .product import *  # NOQA
from .tag import *  # NOQA
from .testcaserun import *  # NOQA
from .testcase import *  # NOQA
from .testcaseplan import *  # NOQA
from .testrun import *  # NOQA
from .user import *  # NOQA
