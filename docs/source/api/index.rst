Kiwi TCMS Python API client
===========================

:mod:`tcms_api` provides a high-level Python interface to the
Kiwi TCMS test case management system. The package also provides
standalone script called 'tcms' which allows easy experimenting with
the interface directly from the Python interpreter by importing
all available objects and enabling the readline support.

In short, after setting your configuration you can easily
manipulate all TCMS objects from the command line, for
example::

    $ tcms
    >>> for case in TestRun(123):
    ...     print(case)


Configuration
~~~~~~~~~~~~~

To be able to contact the Kiwi TCMS server a minimal configuration
file ``~/.tcms.conf`` has to be provided in the user home directory::

    [tcms]
    url = https://tcms.server/xml-rpc/
    username = your-username
    password = your-password

API documentation
~~~~~~~~~~~~~~~~~

Server side RPC methods are documented in :mod:`tcms.xmlrpc.api`.
Client side classes and methods are documented in :mod:`tcms_api`.
