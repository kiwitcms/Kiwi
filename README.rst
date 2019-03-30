Kiwi TCMS - Open Source Test Case Management System
===================================================

.. image:: https://travis-ci.org/kiwitcms/Kiwi.svg?branch=master
    :target: https://travis-ci.org/kiwitcms/Kiwi
    :alt: Travis CI

.. image:: https://readthedocs.org/projects/kiwitcms/badge/?version=latest
    :target: http://kiwitcms.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation

.. image:: https://d322cqt584bo4o.cloudfront.net/kiwitcms/localized.svg
   :target: https://crowdin.com/project/kiwitcms
   :alt: Translate

.. image:: https://pyup.io/repos/github/kiwitcms/Kiwi/shield.svg
    :target: https://pyup.io/repos/github/kiwitcms/Kiwi/
    :alt: Python updates

.. image:: https://badges.greenkeeper.io/kiwitcms/Kiwi.svg
   :alt: Greenkeeper badge
   :target: https://greenkeeper.io/

.. image:: https://scan.coverity.com/projects/15921/badge.svg
    :target: https://scan.coverity.com/projects/kiwitcms-kiwi
    :alt: Coverity scan

.. image:: https://snyk.io/test/github/kiwitcms/Kiwi/badge.svg
    :target: https://snyk.io/test/github/kiwitcms/Kiwi
    :alt: Snyk vulnerability scan

.. image:: https://coveralls.io/repos/github/kiwitcms/Kiwi/badge.svg?branch=master
    :target: https://coveralls.io/github/kiwitcms/Kiwi?branch=master
    :alt: Code coverage

.. image:: https://api.codeclimate.com/v1/badges/3f4e108ea369f625f112/maintainability
   :target: https://codeclimate.com/github/kiwitcms/Kiwi/maintainability
   :alt: Maintainability

.. image:: https://opencollective.com/kiwitcms/tiers/sponsor/badge.svg?label=sponsors&color=brightgreen
   :target: https://opencollective.com/kiwitcms#contributors
   :alt: Become a sponsor


Introduction
------------

.. image:: https://raw.githubusercontent.com/kiwitcms/Kiwi/master/tcms/static/images/kiwi_h80.png
   :alt: "Kiwi TCMS Logo"

Kiwi TCMS is a test plan, test run and test case management system, written in
Python and Django. It features Bugzilla, GitHub, GitLab and JIRA integration, fast test plan
and runs search, powerful access control for each plan, run and case, and XML-RPC APIs.


Brief history
-------------

* Feb 2009 - Project created by Red Hat, Inc. under the name Nitrate
* Nov 2014 - Source code published on GitHub without previous history
* Mar 2016 - Mr. Senko starts contributing to upstream
* Jan 2017 - First private release on MrSenko.com including updates to Django 1.8.x
  and a working automated test suite
* May 2017 - Upstream appears to be unresponsive, so
  `fork <http://mrsenko.com/blog/mr-senko/2017/05/26/nitrate-is-now-kiwitestpad/>`_;
  first release which removes hard-coded bug-tracker specifications and
  makes it possible to integrate with external systems
* Aug 2017 - Support for Django 1.11.x; commit to keeping up to
  date with the latest versions of Django
* Sep 2017 - Project name changed to **Kiwi TCMS**; support for Python 3.5,
  started migrating to modern UI using Patternfly
* Oct 2017 - Launched http://kiwitcms.org and https://demo.kiwitcms.org;
  first bug report from external contributor
* Nov 2017 - Pushed ``kiwitcms/kiwi`` to Docker Hub; merged upstream API client
  sources and modified them to work with the current code base
* Jan 2018 - External contributions are now a fact: German translation by @xbln;
  new team member Anton Sankov
* Mar 2018 - First pull request from non-team member
* Apr 2018 - Enabled pylint and fixed 700 issues in the same release; commit to
  eradicate all of the remaining 3000+ issues and improve code quality
* May 2018 - First public appearance at OSCAL Tirana, DjangoCon Heidelberg and
  PyCon CZ Prague
* Nov 2018 - Project info booth at OpenFest Sofia
* Dec 2018 - GitLab integration support - first big code contribution by
  non-team member; more than 5 different external contributors in 2018 alone
* Feb 2019 - Celebrating 10th anniversary with Kiwi TCMS info booth at FOSDEM Brussels


Documentation
-------------

http://kiwitcms.readthedocs.org/


Installation
------------

See http://kiwitcms.readthedocs.io/en/latest/installing_docker.html


Contribution
------------

See http://kiwitcms.readthedocs.org/en/latest/contribution.html

You are more than welcome to make a monthly donation and help us continue
improving Kiwi TCMS.
[`Become a sponsor <https://opencollective.com/kiwitcms#contributors>`_]


Support
-------

Commercial support for Kiwi TCMS is available from
`Mr. Senko <http://MrSenko.com>`_. For more information, pricing and support
levels info see http://MrSenko.com/.
