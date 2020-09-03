# -*- coding: utf-8 -*-

"""
Kiwi TCMS RPC Service
-------------------------

You need to invoke it using an XML-RPC or JSON-RPC Client! For the available RPC methods
checkout the **Submodules** section!

`tcms-api <https://pypi.org/project/tcms-api/>`_ is the official Python
interface for Kiwi TCMS! We strongly advise that you use it instead of
directly calling the RPC methods below!


How does the RPC interface work?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- The XML-RPC enpoint is at ``https://your-kiwi-instance.com/xml-rpc/``.
- There is also a JSON RPC endpoint at
  ``https://your-kiwi-instance.com/json-rpc/``.
- Most of the RPC methods, like ``filter`` are wrappers around Django's
  QuerySet. They support field lookups as described in
  `Django's documentation
  <https://docs.djangoproject.com/en/dev/ref/models/querysets/#field-lookups>`_.
  For example to get all test cases with summary starting with 'test'::

        >>> TestCase.filter({'summary__startswith': 'test'})

- All RPC methods accept positional parameters as described in their
  documentation. This is the standard behavior for Python. Keyword
  arguments, where supported will be documented explicitly!


How to handle ForeignKey arguments?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The syntax of using ForeignKey in this RPC API follows Django standards::

    foreignkeyname + '__' + fieldname + '__' + field_lookup_syntax

Taking ``TestCase.filter()`` for example, if the query is based on a
``default_tester``'s username which starts with 'John', the syntax will look
like this::

    TestCase.filter({'default_tester__username__startswith': 'John'})

In this example the ``foreignkeyname`` is 'default_tester', ``fieldname`` is
'username' and ``field_lookup_syntax`` is 'startswith'. They are joined
together using double underscores '__'.
"""
