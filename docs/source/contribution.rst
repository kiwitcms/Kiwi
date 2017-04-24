.. _contribution:


Contribution
============

Nitrate team welcomes and appreciates any kind of contribution from you in
order to make Nitrate better and better. Anyone who is interested in Nitrate is
able to contribute in various areas, whatever you are a good and experienced
developer, documentation writer or even a normal user.


Testing
-------

Testing, testing, and testing. Testing is the most important way to ensure the
high quality of Nitrate to serve users. There are many areas to test, such as
the features, documentation, translation, and any other aspects you may focus
on. Once you find a problem, please search it in the `Issues`_ to see whether
it has been reported by other people. If no one reported there yet, you are
encouraged to file one with detailed and descriptive description.

Automated test suite can be execute with the ``make test`` command. The
following syntax is supported::

        make test (uses SQlite)
        TEST_DB=MySQL make test
        TEST_DB=MariaDB make test
        TEST_DB=Postgres make test
        TEST_DB=all make test (will test on all DBs)

.. note::

    If you want to execute testing against different DB engines on your local
    development environment make sure the respecitve DB engines are installed
    and configured! ``make test`` uses the configuration files under
    ``tcms/settings/test/``. Make sure to edit them if necessary!

Documentation
-------------

Documentation has been provided along with the source code within ``docs/``
directory. You could go through the documentation to find any potential
problems, e.g. typos or out-of-date content.

Documentation is built using Sphinx. All content are written in
reStructuredText format. You can use any your favourite text editor to edit it.


Translation
-----------

We are willing to make our contribution to benefit the world. To translate
Nitrate to usual languages in the universe is a critial task. Your contribution
is so important to everyone. Picking up and editing the PO file of specific
language you are skilled in.

Before making pull request, make sure your translation have no grammatical
mistakes and semantic errors. Feel free the look into to translation issues by
consulting language experts around you when you hesitant.


Package
-------

Currently, Nitrate team only supports to distribute standard Python package
and RPM package. You are encouraged to package for other package system, such
as the deb package for Debian based Linux distributions.


Development
-----------

If you are experiencing programming in Python and Django or interested in
learning how to develop a website using Django, contributing patch to fix
problems or improving features are both welcome. Please don't be hesitated to
contact Nitrate team to disucss your ideas and implement it. Following these
steps to contribute code to Nitrate.


Get the code
~~~~~~~~~~~~

Code is hosted in Github. Following the guide in Github to fork and clone
code to your local machine. For example, I have forked Nitrate, then I can
clone it

::

    git clone git@github.com:[my github username]/Nitrate.git


Start Nitrate locally
~~~~~~~~~~~~~~~~~~~~~

See :doc:`set_dev_env` or :doc:`set_dev_env_with_vagrant` for more information!


Confirm the problem
~~~~~~~~~~~~~~~~~~~

Before making any changes to code, you should search in `Issues`_ to see
whether someone else is working on the issue you want to fix. This is helpful
to avoid duplicated work of you. Also, this is a good chance to communicate
with the owner to share what you are thinking of.

If no issue there, create one and give detailed information as much as
possible. If there is already an issue filed, and nobody takes it, then you can
take it if you would like to fix it.


Hack, hack and hack
~~~~~~~~~~~~~~~~~~~

Happy hacking.

#. create local branch based on the ``develop`` branch.

#. hacking, hacking and hacking. Please do remember to write unit tests

#. test, test and test ...

   this command will help you to run project's tests conveniently.

   ::

       make test

#. check your code to ensure it meets PEP8 style.

   ::

       make flake8

#. when your code is ready, commit your changes with sign-off, push to your
   cloned repository, and make a pull request to ``develop`` branch.


Commit message format
~~~~~~~~~~~~~~~~~~~~~

A good commit message will help us to understand your contribution as easily
and correctly as possible. Your commit message should follow this format::

    summary to describe what this commit does

    [Fixed issues or bugs]

    Arbitrary text to describe why you commit these code in detail

Generally, the length of summary line should be limited within range 70-75. The
remaining text should be wrapped at 79 character.

If your pull-request is fixing an issue reported, remember to record in the
second part. It should look like::

    Fix #100


Review & Acceptance
~~~~~~~~~~~~~~~~~~~

Till now, congratulations, you have contributed to Nitrate. Please be patient
to wait for our review.

.. _Issues: https://github.com/Nitrate/Nitrate/issues
