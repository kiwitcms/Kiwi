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
    development environment make sure the respective DB engines are installed
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

Translation
-----------

Kiwi TCMS is using Crowdin as our translation service. You can find the project
at https://crowdin.com/project/kiwitcms. You need to register with Crowdin before
you can work on any translations!

To request a new language be added to Kiwi TCMS please
`create an issue <https://github.com/kiwitcms/Kiwi/issues/new>`_. In the description
let us know your Crowdin username!

Before starting to translate please read the
`Starting Translation how-to
<https://support.crowdin.com/joining-translation-project/#starting-translation>`_
and the `Online Editor guide <https://support.crowdin.com/online-editor/>`_.

.. note::

    All translations need to be proof-read before they are approved! If you do not
    have sufficient Crowdin permissions to do so let us know that you have some new
    translations that you'd like to be approved.

Making strings translatable
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before strings can be translated they need to be marked as translatable.
This is done with the ``gettext()`` function or its shortcut ``_()``.
For templates ``{% load i18n %}`` at the top of the template and then use
the ``{% trans %}`` template tag to mark strings as translatable!
Please read `Django's Translation documentation
<https://docs.djangoproject.com/en/2.0/topics/i18n/translation/>`_ if
you are not sure what these functions are!

.. warning::

    To update .po files once translatable strings have been changed or updated
    you have to execute the following command and commit the results in git::

        ./manage.py makemessages

    At the moment there is no test for this because Django doesn't make it easier
    to implement a quick test based on 'git status'!
