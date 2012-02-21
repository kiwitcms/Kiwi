
==================================================================
 nitrate
==================================================================

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 Python API for the Nitrate test case management system
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Manual section: 1


SYNOPSIS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

nitrate


DESCRIPTION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

python-nitrate provides a high-level Python interface to the
Nitrate test case management system. The package also provides
standalone script 'nitrate' which allows easy experimenting with
the interface directly from the Python interpreter by importing
all available objects and enabling the readline support. In short,
after setting your configuration you can directly manipulate all
nitrate objects, for example::

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

For more detailed and most up-to-date description of all available
nitrate module features see Python online documentation::

    pydoc nitrate


AUTHORS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Written by Petr Splichal <psplicha@redhat.com>. The Python xmlrpc
driver is based on the work of Airald Hapairai, David Malcolm
<dmalcolm@redhat.com>, Will Woods <wwoods@redhat.com> and Bill Peck
<bpeck@redhat.com> and was enhanced by Chenxiong Qi <cqi@redhat.com>,
Tang Chaobin <ctang@redhat.com>, Yuguang Wang <yuwang@redhat.com> and
Xuqing Kuang <xuqingkuang@gmail.com>.
