.. _contribution:


Contribute
==========

Kiwi TCMS team welcomes and appreciates any kind of contribution from you in
order to make Kiwi TCMS better and better. Anyone who is interested in Kiwi TCMS is
able to contribute in various areas, whatever you are a good and experienced
developer, documentation writer or even a normal user.

.. include:: set_dev_env.rst
    :start-line: 2

Testing
-------

Automated test suite can be executed with the ``make check`` command. The
following syntax is supported::

        make check (uses SQlite)
        TEST_DB=MySQL make check
        TEST_DB=MariaDB make check
        TEST_DB=Postgres make check
        TEST_DB=all make check (will test on all DBs)

.. note::

    If you want to execute testing against different DB engines on your local
    development environment make sure the respecitve DB engines are installed
    and configured! ``make check`` uses the configuration files under
    ``tcms/settings/test/``. Make sure to edit them if necessary!


Security Issues
---------------

If you think that an issue with Kiwi TCMS may have security implications, please
do not publically report it in the bug tracker. Instead ping us via email to
coordinate the fix and disclosure of the issue!


Reporting General Issues
------------------------

If you have any good idea, or catch a bug, please do
create an issue at https://github.com/kiwitcms/Kiwi/issues!


Documentation
-------------

Documentation has been provided along with the source code within the ``docs/``
directory and is built using Sphinx. All content is written in
reStructuredText format. To build the docs::

    $ cd docs/
    $ make html
