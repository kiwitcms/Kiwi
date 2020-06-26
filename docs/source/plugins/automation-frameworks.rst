Automation Frameworks plugins
=============================

Kiwi TCMS can be used with test automation frameworks. Test names and results
are fetched automatically from the test automation framework using a plugin!
This is an additional software package that you have to install in your test
environment and configure it to talk back to Kiwi TCMS.


Available plugins
-----------------

* `tap-plugin <https://github.com/kiwitcms/tap-plugin>`_: for reading
  Test Anything Protocol (TAP) files. Written in Python
* `junit.xml-plugin <https://github.com/kiwitcms/junit.xml-plugin>`_:
  for reading junit.xml formatted files. Written in Python
* Native `JUnit 5 plugin <https://github.com/kiwitcms/junit-plugin/>`_ written
  in Java
* `Robot Framework plugin <https://github.com/kiwitcms/robotframework-plugin>`_
* `Django test runner plugin <https://github.com/kiwitcms/django-plugin>`_

.. WHEN UPDATING THIS SECTION MAKE SURE IT MATCHES https://kiwitcms.org/features/


Plugins still in progress
-------------------------

* Native `PHPUnit plugin <https://github.com/kiwitcms/phpunit-plugin/>`_ written
  in PHP
* Native `py.test plugin <https://github.com/kiwitcms/pytest-plugin/>`_ written
  in Python

Watch their repositories or
`subscribe to our newsletter <https://kiwitcms.us17.list-manage.com/subscribe/post?u=9b57a21155a3b7c655ae8f922&id=c970a37581>`_
to be notified when they are officially released.

.. WHEN UPDATING THIS SECTION MAKE SURE IT MATCHES https://kiwitcms.org/features/


Proposed plugins
----------------

* Native `Test NG plugin <https://github.com/kiwitcms/Kiwi/issues/692>`_ to be
  written in Java
* `GitHub status plugin <https://github.com/kiwitcms/Kiwi/issues/817>`_

.. WHEN UPDATING THIS SECTION MAKE SURE IT MATCHES https://kiwitcms.org/features/

Vote with a ``:+1:`` reaction on GitHub to give them priority!


Plugin configuration
--------------------

Plugins will perform 2 high-level actions:

1) Parse the test results from the test runner/automation framework
2) Send these results to Kiwi TCMS via the API

The second is controlled via environment variables and behavior is described
`here
<http://kiwitcms.org/blog/atodorov/2018/11/05/test-runner-plugin-specification/>`_.
Important variables are:

* ``TCMS_PLAN_ID`` - if defined will create test runs under this TestPlan
* ``TCMS_RUN_ID`` - if defined will report results to this TestRun
* ``TCMS_PRODUCT`` or ``TRAVIS_REPO_SLUG`` or ``JOB_NAME`` - defines the
  product under test if we have to create new objects in the database
* ``TCMS_PRODUCT_VERSION`` or ``TRAVIS_COMMIT`` or ``TRAVIS_PULL_REQUEST_SHA``
  or ``GIT_COMMIT`` - defines the version under test
* ``TCMS_BUILD`` or ``TRAVIS_BUILD_NUMBER`` or ``BUILD_NUMBER`` - defines
  the build which we are testing


You are free to adjust these variables and how they get assigned different values
in your CI workflow. This will change how/where results are reported.
For example this is how the environment for
`kiwitcms-tap-plugin
<https://github.com/kiwitcms/tap-plugin/blob/master/tests/bin/make-tap>`_
looks like::

    #!/bin/bash

    if [ "$TRAVIS_EVENT_TYPE" == "push" ]; then
        # same as $TRAVIS_TAG when building tags
        export TCMS_PRODUCT_VERSION=$TRAVIS_BRANCH
    fi

    if [ "$TRAVIS_EVENT_TYPE" == "pull_request" ]; then
        export TCMS_PRODUCT_VERSION="PR-$TRAVIS_PULL_REQUEST"
    fi

    export TCMS_BUILD="$TRAVIS_BUILD_NUMBER-$(echo $TRAVIS_COMMIT | cut -c1-7)"

The above configuration creates a separate TestPlan for each branch,
a separate TestPlan for each pull request (recording possible multiple test
runs) and separate TestPlan and TestRun for each tag on GitHub!
