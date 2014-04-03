===============
    nitrate
===============

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Command line interpreter for the Nitrate Python API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Manual section: 1
:Manual group: User Commands
:Date: February 2012


SYNOPSIS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
nitrate


DESCRIPTION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
python-nitrate provides a high-level Python interface to the
Nitrate test case management system. The package also provides
standalone script 'nitrate' which allows easy experimenting with
the interface directly from the Python interpreter by importing
all available objects and enabling the readline support.

In short, after setting your configuration you can easily
manipulate all Nitrate objects from the command line, for
example::

    $ nitrate
    >>> for case in TestRun(123):
    ...     print case


CONFIGURATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To be able to contact the Nitrate server a minimal user config
file ~/.nitrate has to be provided in the user home directory::

    [nitrate]
    url = https://nitrate.server/xmlrpc/


SEE ALSO
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
python-nitrate


AUTHOR
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Petr Šplíchal <psplicha@redhat.com>
