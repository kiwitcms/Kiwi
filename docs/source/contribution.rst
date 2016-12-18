.. _contribution:


Contribution
============

Nitrate team welcomes and appreciates any kind of contribution from community
to make Nitrate better and better. Any one who is interested in Nitrate is able
to contribute in various areas, whatever you are a good and experienced
developers, documentation writer or even a normal user.


Testing
-------

Testing, testing, and testing. Testing is the most important way to ensure the
high quality of Nitrate to serve the community. There are many areas to test,
such as the features, documentation, translation, and others you may
focus on. Once you find a problem, please do search it in the `Issues`_ to
see whether it has been reported by other people and the discussion on it. If
no one reported there yet, you are encouraged to file one with detailed and
descriptive comment to give a clear description.

.. _Issues: https://github.com/Nitrate/Nitrate/issues


Documentation
-------------

Documentation has been provided along with the source code within ``docs/``
directory. You could go through the documentation to find any potential typos
or out-of-date content. This is good chance for you to become outstanding
Nitrate documentation writer to help users and developers from community
understand and use Nitrate smoothly and easily.

Documentation is built using Sphinx. All content are written in
reStructuredText format. You can open and edit them by using any your favorite
text editor.


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

Currently, Nitrate team only support to distribute in standard Python package
and RPM package by providing a well maintained SPEC file. You are encouraged to
package for other package system, such as the deb package for Debian based
Linux distributions.


Development
-----------

If you are a experienced programmer in Python and Django, even if you are
interested in learning how to develop a website using Django, contribute patch
to fix problems or improve features are both welcome. Please dont' be hesitated
to contact Nitrate team to disucss your ideas. Contribute code to Nitrate,
please do following steps.


Get code
~~~~~~~~

Code is being hosted in Github. Following the guide in Github to fork and clone
code to your local machine.

For example, I have forked project and then I can clone to my local by issuing

::

    git clone https://github.com/my_username/Nitrate.git


Confirm the problem
~~~~~~~~~~~~~~~~~~~

#. Before making any changes to the code, you should search in Issues to see
   whether someone else is working on the issue you want to fix. This is
   helpful to avoid duplicated work of you. Also, this is a good chance to
   communicate with the owner to share what you are thinking of.

#. If no bug there, create a bug and give detailed information as much as
   possible. If there is already a bug filed, and nobody takes it, then you may
   take it and change status to ``ASSIGNED``.


Hack, hack and hack
~~~~~~~~~~~~~~~~~~~

Happy hacking.

#. create local branch based on the master branch.

#. hacking, hacking and hacking with writing unit tests ...

#. test, test and test ...

   this command will help you to run project's whole unit tests conveniently.

   ::

       make test

#. ensure your code is passed the check of PEP8, running this command to help
   you check code style much conveniently.

   ::

       make flake8

#. when your code is ready, push to your code repository, and then make a pull
   request to ``develop`` branch.

A good commit message will help us to understand your contribution easily and
correctly. You commit message should follow this format::

    summary to describe what this commit does

    Arbitrary text to describe why you commit these code in detail

The first line is the summary of commit. This is necessary as you are doing in
other projects. Give a short and descriptive enough words. Then, a blank line
there. And next is the detail part containing detail information of what and
why this commit fixes or provides new feature.

The length of summary line should be limited within range 70-75. The remaining
text should be wrapped at 79 character.

The last thing is don't forget add issue number in summary. For example,

::

    fix #1 improve testcase loading performance

Review & Acceptance
~~~~~~~~~~~~~~~~~~~

Till now, congratulations to you that you have contributed to Nitrate project
in stage. However, Nitrate team will take time to review your pull request. We
will review contributions as soon as possible, however there is not guarantee
that each patch will be reviewed and give response to contributor in a very
short time.

Well, please be patient to wait for our review. The reivew process will happen
in the pull request totally, so all your experience working with Github applies
to this review process too.

Once problems found, the response will be commented. Please fix all problems,
then rebase upon the latest code and make a new pull request.

If everything is okay, we are happy to accept your code and merge into
``develop`` branch.
