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

.. image:: https://snyk.io/test/github/kiwitcms/Kiwi/badge.svg?targetFile=tcms/package.json
    :target: https://snyk.io/test/github/kiwitcms/Kiwi/?targetFile=tcms/package.json
    :alt: Snyk vulnerability scan

.. image:: https://coveralls.io/repos/github/kiwitcms/Kiwi/badge.svg?branch=master
    :target: https://coveralls.io/github/kiwitcms/Kiwi?branch=master
    :alt: Code coverage

.. image:: https://api.codeclimate.com/v1/badges/3f4e108ea369f625f112/maintainability
   :target: https://codeclimate.com/github/kiwitcms/Kiwi/maintainability
   :alt: Maintainability

.. image:: https://tidelift.com/badges/package/pypi/kiwitcms
    :target: https://tidelift.com/subscription/pkg/pypi-kiwitcms?utm_source=pypi-kiwitcms&utm_medium=github&utm_campaign=readme
    :alt: Tidelift

.. image:: https://opencollective.com/kiwitcms/tiers/sponsor/badge.svg?label=sponsors&color=brightgreen
   :target: https://opencollective.com/kiwitcms#contributors
   :alt: Become a sponsor

.. image:: https://img.shields.io/twitter/follow/KiwiTCMS.svg
    :target: https://twitter.com/KiwiTCMS
    :alt: Kiwi TCMS on Twitter


Introduction
------------

.. image:: https://raw.githubusercontent.com/kiwitcms/Kiwi/master/tcms/static/images/kiwi_h80.png
   :alt: "Kiwi TCMS Logo"

Kiwi TCMS is the leading open source test case management system. It is written in
Python and Django. It features bug tracker integration, fast test plan
and runs search, powerful access control, test automation framework plugins and
rich API layer.


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
* Jun 2019 - `OpenAwards winner <http://kiwitcms.org/blog/atodorov/2019/06/24/kiwi-tcms-is-openawards-2019-best-tech-community-winner/>`_
  in 'Best Tech Community' category


Live demo
---------

https://public.tenant.kiwitcms.org


Documentation
-------------

http://kiwitcms.readthedocs.org/


Installation
------------

See
`Running Kiwi TCMS as a Docker container <http://kiwitcms.readthedocs.io/en/latest/installing_docker.html>`_.


Language support
----------------

- `Supported languages <https://crowdin.com/project/kiwitcms>`_
- `Request new language <https://github.com/kiwitcms/Kiwi/issues/new?title=Request+new+language:+...&body=Please+enable+...+language+in+Crowdin>`_
- `Translation guide <https://kiwitcms.readthedocs.io/en/latest/contribution.html#translation>`_


Help us improve Kiwi TCMS
-------------------------

- Click the `Star` button at https://github.com/kiwitcms/Kiwi/stargazers
- Click the star icon at https://hub.docker.com/r/kiwitcms/kiwi/
- Follow @KiwiTCMS at https://twitter.com/KiwiTCMS
- Subscribe to our
  `newsletter <https://kiwitcms.us17.list-manage.com/subscribe/post?u=9b57a21155a3b7c655ae8f922&id=c970a37581>`_
- Send us testimonials and feedback about how your team is using Kiwi TCMS
- Donate 5$ or more at https://opencollective.com/kiwitcms
- Become a `contributor <http://kiwitcms.readthedocs.org/en/latest/contribution.html>`_


Support
-------

Commercial support for Kiwi TCMS is also available.
For more information see http://kiwitcms.org.
