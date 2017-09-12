.. _contribution:


Contribute
==========

KiwiTestPad team welcomes and appreciates any kind of contribution from you in
order to make KiwiTestPad better and better. Anyone who is interested in KiwiTestPad is
able to contribute in various areas, whatever you are a good and experienced
developer, documentation writer or even a normal user.

.. include:: set_dev_env.rst

Testing
-------

Automated test suite can be executed with the ``make test`` command. The
following syntax is supported::

        make check (uses SQlite)
        TEST_DB=MySQL make check
        TEST_DB=MariaDB make check
        TEST_DB=Postgres make check
        TEST_DB=all make check (will test on all DBs)

.. note::

    If you want to execute testing against different DB engines on your local
    development environment make sure the respecitve DB engines are installed
    and configured! ``make test`` uses the configuration files under
    ``tcms/settings/test/``. Make sure to edit them if necessary!


Security Issues
---------------

If you think that an issue with KiwiTestPad may have security implications, please
do not publically report it in the bug tracker. Instead ping us via email to
coordinate the fix and disclosure of the issue!


Reporting General Issues
------------------------

If you have any good idea, or catch a bug, please do
create an issue at https://github.com/kiwitcms/Kiwi/issues!


Documentation
-------------

Documentation has been provided along with the source code within the ``docs/``
directory and is built using Sphinx. All content are written in
reStructuredText format. You can use any your favourite text editor to edit it.
To build the docs::

    $ cd docs/
    $ make html
