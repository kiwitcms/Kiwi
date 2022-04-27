Change Log
==========

Kiwi TCMS 11.3 (27 Apr 2022)
----------------------------

.. important::

    This is a small release which contains security related updates, several improvements,
    bug fixes and new translations!


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py upgrade

Security
~~~~~~~~

- Update django from 4.0.3 to 4.0.4, see
  https://docs.djangoproject.com/en/4.0/releases/4.0.4/


Improvements
~~~~~~~~~~~~

- Update bleach from 4.1.0 to 5.0.0
- Update django-tree-queries from 0.7.0 to 0.9.0
- Update jira from 3.1.1 to 3.2.0
- Update pygments from 2.11.2 to 2.12.0
- Update python-gitlab from 3.2.0 to 3.3.0
- Update tzdata from 2021.5 to 2022.1
- Update node_modules/marked from 4.0.12 to 4.0.14
- Update node_modules/prismjs from 1.27.0 to 1.28.0
- Allow overriding of Azure Boards API version. Closes
  `Issue #2717 <https://github.com/kiwitcms/Kiwi/issues/2717>`_
- If ``tenant_groups`` is enabled then ``refresh_permissions`` command will
  update default tenant groups too
- Document tenant-group permissions


Settings
~~~~~~~~

- New setting ``AZURE_BOARDS_API_VERSION``, defaults to 6.0. Can be overriden
  directly in settings or via environment variable with the same name


Bug fixes
~~~~~~~~~

- Patch for repositories under GitLab subgroups. Fixes
  `Issue #2643 <https://github.com/kiwitcms/Kiwi/issues/2643>`_ (@cmeissl)
- Don't crash if a comment user has been removed. Fixes
  `KIWI-TCMS-HZ <https://sentry.io/organizations/kiwitcms/issues/3086416250/>`_


Refactoring
~~~~~~~~~~~

- Split Users & Groups menu items under ADMIN entry in navigation
- [pre-commit.ci] updates
- pylint adjustments


Translations
~~~~~~~~~~~~

- Updated `Chinese Simplified translation <https://crowdin.com/project/kiwitcms/zh-CN#>`_



Kiwi TCMS 11.2 (09 Mar 2022)
----------------------------

.. important::

    This is a small release which contains several improvements, new API methods,
    internal refactoring and new translations!


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py upgrade


Improvements
~~~~~~~~~~~~

- Update django from 4.0.2 to 4.0.3
- Update django-grappelli from 3.0.2 to 3.0.3
- Update django-simple-captcha from 0.5.14 to 0.5.17
- Update python-bugzilla from 3.1.0 to 3.2.0
- Update python-gitlab from 3.1.1 to 3.2.0
- Update node_modules/prismjs from 1.26.0 to 1.27.0
- Add new command to perform a collection of post-upgrade tasks.
  Kiwi TCMS admins are advised to replace
  ``manage.py migrate`` with ``manage.py upgrade`` (Ivajlo Karabojkov)


API
~~~

- New API method ``Category.create()``. Fixes
  `Issue #2705 <https://github.com/kiwitcms/Kiwi/issues/2705>`_ (Erik Heeren)
- New API method ``Classification.create()``. Fixes
  `Issue #2705 <https://github.com/kiwitcms/Kiwi/issues/2705>`_ (Erik Heeren)


Refactoring and testing
~~~~~~~~~~~~~~~~~~~~~~~

- Add docker build & push automation
- Fix Bandit exclusion rule
- Test and build on aarch64
- Apply auto fixes fro pre-commit.ci
- Apply auto fixes from Deepsource
- Update versions of several GitHub Actions
- Use the appropriate path to package.json for Dependabot
- Remove old Telemetry link in menu to avoid confusion


Translations
~~~~~~~~~~~~

- Updated `Bulgarian translation <https://crowdin.com/project/kiwitcms/bg#>`_
- Updated `Japanese translation <https://crowdin.com/project/kiwitcms/ja#>`_
- Updated `Chinese Traditional translation <https://crowdin.com/project/kiwitcms/zh-TW#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_
- Updated `Spanish translation <https://crowdin.com/project/kiwitcms/es-ES#>`_



Kiwi TCMS 11.1 (02 Feb 2022)
----------------------------

.. important::

  This is a small release which contains security related updates, several improvements,
  bug fixes and new translations!

Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate
    ./manage.py refresh_permissions


Security
~~~~~~~~

- Update Django from 3.2.10 to 4.0.2 to fix several fulnerabilities:
  CVE-2022-22818, CVE-2022-23833, CVE-2021-45115, CVE-2021-45116,
  CVE-2021-45452. Of those we believe that only
  *CVE-2022-23833: Denial-of-service possibility in file uploads* may directly
  impact Kiwi TCMS


Improvements
~~~~~~~~~~~~

- Update django-contrib-comments from 2.1.0 to 2.2.0
- Update django-uuslug from 1.2.0 to 2.0.0
- Update python-gitlab from 3.1.0 to 3.1.1
- Update node_modules/marked from 4.0.10 to 4.0.12


Database
~~~~~~~~

- New migration for django-simple-captcha


Settings
~~~~~~~~

- ``RECAPTCHA_PUBLIC_KEY``, ``RECAPTCHA_PRIVATE_KEY`` and ``RECAPTCHA_USE_SSL``
  are no longer in use
- New setting ``USE_CAPTCHA``, defaults to True
- The string "captcha" is added to ``INSTALLED_APPS``


Bug fixes
~~~~~~~~~

- Fix inappropriate RPC calls causing Version and Build dropdown widgets to
  display no values. Fixes
  `Issue #2704 <https://github.com/kiwitcms/Kiwi/issues/2704>`_


Refactoring and testing
~~~~~~~~~~~~~~~~~~~~~~~

- Add ``tzdata`` to requirements
- Replace django-recaptcha with django-simple-captcha
- Adjust /init-db view to reliably detect when applying database migrations
  is complete and not exit prematurely


Translations
~~~~~~~~~~~~

- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_



Kiwi TCMS 11.0 (24 Jan 2022)
----------------------------

.. important::

  This is a new major release which contains security related updates, several improvements,
  API changes, bug fixes and new translations!

Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate
    ./manage.py refresh_permissions


Improvements
~~~~~~~~~~~~

- Update Django to 3.2.11
- Update django-colorfield from 0.4.5 to 0.6.3
- Update django-grappelli from 2.15.3 to 3.0.2
- Update psycopg2 from 2.9.2 to 2.9.3
- Update pygments from 2.10.0 to 2.11.2
- Update python-gitlab from 2.10.1 to 3.1.0
- Update node_modules/prismjs from 1.25.0 to 1.26.0
- Update node_modules/marked from 2.1.3 to 4.0.10
- Admin panel now allows to view, add, edit and delete Environment records
- Allow selection of environment when creating new TestRun and display the chosen
  values inside the TestRun page. Closes
  `Issue #1344 <https://github.com/kiwitcms/Kiwi/issues/1344>`_
- Creating a TestRun will now generate test execution matrix based on the available
  environment and test case properties. Closes
  `Issue #1843 <https://github.com/kiwitcms/Kiwi/issues/1843>`_
- When generating a test execution matrix the supported algorithms are
  "full" and "pairwise". Closes
  `Issue #1931 <https://github.com/kiwitcms/Kiwi/issues/1931>`_

  - Feature is enabled for test runs which contain test cases. This
    feature is not shown when creating an empty test run
  - This feature isn't supported when subsequently adding new test cases
    to test run
- Record a random hex number under ``/Kiwi/uploads/installation-id``


Database
~~~~~~~~

- New model ``testrun.Environment``
- New model ``testrun.EnvironmentProperty``
- New model ``testrun.Property``


Settings
~~~~~~~~

- Update the value of ``MODERNRPC_METHODS_MODULES`` setting to include
  modules with the new API methods


API
~~~

- Method ``TestRun.add_case`` will now return a list.

  .. warning::

    This breaks API compatibility with older versions and will break
    all plugins which rely on this method. Use plugins v11 or greater!
- Method ``TestRun.add_case`` return value will now include a field named
  ``properties``
- New methods ``Environment.properties``, ``Environment.add_property`` and
  ``Environment.remove_property``
- New method ``TestRun.properties``


Bug fixes
~~~~~~~~~

- Send e-mail notification when adding comments to bugs. Fixes
  `Issue #2232 <https://github.com/kiwitcms/Kiwi/issues/2232>`_ (@cmbahadir)
- Disable the "+" button when there is no related element selected. Fixes
  `Issue #2561 <https://github.com/kiwitcms/Kiwi/issues/2561>`_ (@cmbahadir)
- When cloning test plans keep the existing test case sort order inside
  the resulting test plan. Fixes
  `Issue #2218 <https://github.com/kiwitcms/Kiwi/issues/2218>`_ (Nicolas Gelot)
- Configure en_US.UTF-8 locale inside container. Allows upload of files with
  unicode names. Fixes
  `Issue #2600 <https://github.com/kiwitcms/Kiwi/issues/2600>`_


Refactoring and testing
~~~~~~~~~~~~~~~~~~~~~~~

- Refresh logo design
- Pylint fixes
- Pin setuptools b/c of problem with django-extensions
- Remove redundant test scenario
- Shell script refactoring


Translations
~~~~~~~~~~~~

- Updated `Chinese Simplified translation <https://crowdin.com/project/kiwitcms/zh-CN#>`_
- Updated `Chinese Traditional translation <https://crowdin.com/project/kiwitcms/zh-TW#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Hebrew translation <https://crowdin.com/project/kiwitcms/he#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_



Kiwi TCMS 10.5 (25 Nov 2021)
----------------------------

.. important::

    This is a medium sized release which contains various improvements and new features,
    database changes, new settings and API methods, bug-fixes, internal refactoring and
    updated translations.

Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate
    ./manage.py refresh_permissions


Improvements
~~~~~~~~~~~~

- Update django from 3.2.7 to 3.2.9
- Update django-colorfield from 0.4.3 to 0.4.5
- Update django-extensions from 3.1.3 to 3.1.5
- Update django-grappelli from 2.15.1 to 2.15.3
- Update django-tree-queries from 0.6.0 to 0.7.0
- Update jira from 3.0.1 to 3.1.1
- Update markdown from 3.3.4 to 3.3.6
- Update mysqlclient from 2.0.3 to 2.1.0
- Update psycopg2 from 2.9.1 to 2.9.2
- Display a warning if connection doesn't use HTTPS (Ivajlo Karabojkov)
- Account registration page can be turned on/off via settings. Fixes
  `Issue #2500 <https://github.com/kiwitcms/Kiwi/issues/2500>`_
- TestCase Search page can now filter by TestPlan. Fixes
  `Issue #2283 <https://github.com/kiwitcms/Kiwi/issues/2283>`_
- Allow template selection when creating new test case. Fixes
  `Issue #957 <https://github.com/kiwitcms/Kiwi/issues/957>`_
- TestCase page now allows specification of properties, e.g. mobile devices
  on which the test should be executed. This feature serves as a building
  block for
  `Issue #1843 <https://github.com/kiwitcms/Kiwi/issues/1843>`_,
  `Issue #1931 <https://github.com/kiwitcms/Kiwi/issues/1931>`_ and
  `Issue #1344 <https://github.com/kiwitcms/Kiwi/issues/1344>`_ but isn't active anywhere else inside
  Kiwi TCMS at the moment
- TestExecution properties will be displayed inside TestRun page if they
  have been specified
- Rearrange help-text in admin page for better visibility
- Switch to official Postgres image from Docker Hub
- Switch to official MariaDB image from Docker Hub

.. warning::

    For Postgres data dir changed from ``/var/lib/pgsql/data`` to ``/var/lib/postgres/data``.
    Environment variables inside docker-compose file changed as well,
    see ``docker-compose.postgres``.

    For MariaDB data dir changed from ``/var/lib/mysql/data`` to ``/var/lib/mysql``.
    ``MYSQL_CHARSET`` & ``MYSQL_COLLATION`` environment variables are no longer
    recognized. Instead they are present as command line options passed to the container,
    see ``docker-compose.yml``. Previous workaround for these variables was also removed.

    If you want to migrate from the previous ``centos/mariadb-103-centos7`` or
    ``centos/postgresql-12-centos7`` containers to ``mariadb:latest`` and ``postgres:latest``
    make sure to update your container control files!


Settings
~~~~~~~~

- New setting ``REGISTRATION_ENABLED``, default ``True``, Can be controlled via
  environment variable ``KIWI_REGISTRATION_ENABLED``. When set to ``False``
  will disable account registration page


Database
~~~~~~~~

- New model ``testcases.Property``
- New model ``testcases.Template``
- New model ``testruns.TestExecutionProperty``
- Remove ``unique_together`` constraint for ``testruns.TestExecution`` model.
  This makes it possible to add multiple executions for the same test case in
  the same test run

.. warning::

    These newly added models create additional permission labels with names
    *testcases | template | Can .... template*,
    *testcases | property | Can .... property*,
    *testruns | test execution property | Can .... test execution property*

    Execute ``manage.py refresh_permissions`` and/or assign them manually to
    users and groups if they should be able to interact with the new objects!


API
~~~

- Method ``TestCase.filter()`` now returns additional fields
  ``setup_duration``, ``testing_duration``, ``expected_duration`` - all
  serialized in seconds. Refs
  `Issue #1923 <https://github.com/kiwitcms/Kiwi/issues/1923>`_ (Mfon Eti-mfon)
- Method ``User.filter()`` will no longer return fields
  ``groups``, ``user_permissions``, ``date_joined`` and ``last_login``
- New method ``TestExecution.properties()``
- New method ``TestCase.properties()``
- New method ``TestCase.add_property()``
- New method ``TestCase.remove_property()``


Bug fixes
~~~~~~~~~

- Unify tab size & tab indentation b/w Python & SimpleMDE. Fixes
  `Issue #1802 <https://github.com/kiwitcms/Kiwi/issues/1802>`_
- Use ``sane_list extension`` for rendering consecutive lists in markdown. Closes
  `Issue #2511 <https://github.com/kiwitcms/Kiwi/issues/2511>`_

.. warning::
    The visual markdown editor explicitly didn't follow markdown syntax rules
    by allowing indentation with 2 spaces and treating tabs as 2 spaces as well.
    See "Indentation/Tab Length" at https://python-markdown.github.io/#differences

    The backend markdown rendering engine explicitly followed an undefined behavior
    which happens to be different from what the visual markdown editor does.
    See "Consecutive Lists" at https://python-markdown.github.io/#differences

    The previous 2 changes make sure the visual editor and backend rendering engine
    follow the same rules. This may result is "broken" display of existing text which
    doesn't follow the markdown syntax rules. If you spot such text just edit to make
    it render the way you wish.

- Fix broken URL and minor updates to documentation
- Update GitLab tracker integration documentation to avoid confusion. Closes
  `Issue #2559 <https://github.com/kiwitcms/Kiwi/issues/2559>`_
- Limit tag input length to 255 characters. Closes
  `Issue #2176 <https://github.com/kiwitcms/Kiwi/issues/2176>`_
- Make error notifications in Admin to display with red color
- Select only visible rows for bulk-update in TestRun page. Fixes
  `Issue #2222 <https://github.com/kiwitcms/Kiwi/issues/2222>`_
- Remove ``Cache-Control`` header from httpd. Closes
  `Issue #443 <https://github.com/kiwitcms/Kiwi/issues/443>`_


Refactoring and testing
~~~~~~~~~~~~~~~~~~~~~~~

- Add permissions test for add-hyperlink-bulk menu. Closes
  `Issue #716 <https://github.com/kiwitcms/Kiwi/issues/716>`_
- Add explicit tests for issue tracker integration with GitLab.com
- Tests teardown - remove comments & close issues on GitLab.com
- Add missing ``rlPhaseEnd`` for docker tests
- Multiple pylint and eslint fixes


Translations
~~~~~~~~~~~~

- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Hungarian translation <https://crowdin.com/project/kiwitcms/hu#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_



Kiwi TCMS 10.4 (04 Oct 2021)
----------------------------

.. important::

   This is a small release which includes several improvements, bug fixes,
   internal refactoring and updated translations.


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Security
~~~~~~~~

- Update prismjs from 1.24.1 to 1.25.0. Includes patches against a
  Regular Expression Denial of Service vulnerability.
  See https://snyk.io/vuln/SNYK-JS-PRISMJS-1585202


Improvements
~~~~~~~~~~~~

- Update bleach from 4.0.0 to 4.1.0
- Update django from 3.2.6 to 3.2.7
- Update django-colorfield from 0.4.2 to 0.4.3
- Update pygithub from 1.54.1 to 1.55
- Update pygments from 2.9.0 to 2.10.0
- Update python-gitlab from 2.10.0 to 2.10.1
- Allow filtering by TestRun ID in Test Case Search page
- Update test execution prefix in list of executions on TestRun page.
  Now includes both TE and TC numbers before the summary link
- Allow search by translated names on Test Run page
- Redirect "ADMIN -> Users and groups" menu item according to tenancy
- Allow creation of new test run from selected test cases inside existing test
  run. For example only select cases which are currently failing and re-test
  against a different build!
- The ``initial_setup`` command will create a schema called "empty" when executed
  inside a multi-tenant setup. Refs
  `Issue #127 <https://github.com/kiwitcms/tenants/issues/127>`_


Settings
~~~~~~~~

- Update values for ``MODERNRPC_HANDLERS`` setting
- Rename ``SafeJSONRPCHandler`` to ``KiwiTCMSJsonRpcHandler``
- New RPC handler class ``KiwiTCMSXmlRpcHandler``

.. warning::

    If you had manipulated the value of MODERNRPC_HANDLERS make sure that
    you update to the new class names!


Database
~~~~~~~~

- New migrations for altered meta options


API
~~~

- ``TestCase.create`` method accepts ``setup_duration`` and ``testing_duration`` fields.
  Refs `Issue #1923 <https://github.com/kiwitcms/Kiwi/issues/1923>`_ (Mfon Eti-mfon)
- ``TestCase.update`` method acepts  ``setup_duration`` and ``testing_duration`` fields.
  Refs `Issue #1923 <https://github.com/kiwitcms/Kiwi/issues/1923>`_ (Mfon Eti-mfon)
- New method ``Testing.individual_test_case_health``
- Timedelta values are serialized to float, representing seconds


Bug fixes
~~~~~~~~~

- Fix wrong URL parameter passed to test cases clone page
- Show translated execution statuses for TestRun page. Closes
  `Issue #1966 <https://github.com/kiwitcms/Kiwi/issues/1966>`_
- Properly initialize Product value on TestRun Edit page. Closes
  `Issue #2514 <https://github.com/kiwitcms/Kiwi/issues/2514>`_
- Clone duration fields when cloning a test case


Refactoring and testing
~~~~~~~~~~~~~~~~~~~~~~~


- New automated test scenario for ``kiwi_auth.admin`` (Mariyan Garvanski)
- Unify similar strings to reduce transaltions burden
- Inside buildroot ``PyNaCl`` needs ``make`` in order to build a wheel package
- Adjust values for parametrized test to match existing scenarios
- Fix code smells from newer pylint
- eslint fixes for the JavaScript files


Translations
~~~~~~~~~~~~


- Updated `Chinese Simplified translation <https://crowdin.com/project/kiwitcms/zh-CN#>`_
- Updated `German translation <https://crowdin.com/project/kiwitcms/de#>`_
- Updated `Italian translation <https://crowdin.com/project/kiwitcms/it#>`_
- Updated `Portuguese, Brazilian translation <https://crowdin.com/project/kiwitcms/pt-BR#>`_
- Updated `Russian translation <https://crowdin.com/project/kiwitcms/ru#>`_



Kiwi TCMS 10.3 (11 Aug 2021)
----------------------------

.. important::

    This is a small release which includes several improvements, bug fixes,
    internal refactoring and updated translations.

    It is the twelveth release to include contributions via our
    `open source bounty program`_!


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update bleach from 3.3.0 to 4.0.0
- Update django from 3.2.5 to 3.2.6
- Update django-colorfield from 0.4.1 to 0.4.2
- Update django-tree-queries from 0.5.2 to 0.6.0
- Update python-bugzilla from 3.0.2 to 3.1.0
- Update python-gitlab from 2.9.0 to 2.10.0
- Update node_modules/html5sortable from 0.13.2 to 0.13.3
- Docker image is now based on Red Hat's Universal Base Image instead of
  CentOS 8. See https://www.redhat.com/en/blog/introducing-red-hat-universal-base-image and
  https://catalog.redhat.com/software/containers/ubi8/ubi-minimal/5c359a62bed8bd75a2c3fba8.

  .. important::

      The ``mysql`` and ``psql`` binaries in the container image are not available anymore!
      Backup and restore instructions have been updated accordingly, see
      https://kiwitcms.org/blog/atodorov/2018/07/30/how-to-backup-docker-volumes-for-kiwi-tcms/.

- Use ``initial_setup`` command to create public tenant in case we're running a multi-tenant
  instance. References
  `Enterprise #88 <https://github.com/kiwitcms/enterprise/issues/88>`_ (Ivajlo Karabojkov)
- Document that for Jira integration we use API tokens


Bug fixes
~~~~~~~~~

- Fix a bug where drop-down selectors for test plans would not show any values when
  product is changed. Fixes
  `Issue #2467 <https://github.com/kiwitcms/Kiwi/issues/2467>`_


Refactoring and testing
~~~~~~~~~~~~~~~~~~~~~~~

- Add tests for missing coverage in ``kiwi_auth.admin``. References
  `Issue #1607 <https://github.com/kiwitcms/Kiwi/issues/1607>`_
  (Mariyan Garvanski)
- Fix some eslint issues and formatting in ``testcases/js/get.js``
- Use shorter URL when cloning test cases from TP page. References
  `Issue #1054 <https://github.com/kiwitcms/Kiwi/issues/1054>`_
- Limit URI size to 10KiB. This alone should allow for more than 1000 PKs
  specified for cloning. In addition Django itself limits the maximum number of
  GET/POST fields to 1000 via the ``DATA_UPLOAD_MAX_NUMBER_FIELDS`` setting,
  see https://docs.djangoproject.com/en/3.2/ref/settings/#data-upload-max-number-fields.
  Closes
  `Issue #1054 <https://github.com/kiwitcms/Kiwi/issues/1054>`_


Translations
~~~~~~~~~~~~

- Updated `Chinese Simplified translation <https://crowdin.com/project/kiwitcms/zh-CN#>`_
- Updated `German translation <https://crowdin.com/project/kiwitcms/de#>`_
- Updated `Hungarian translation <https://crowdin.com/project/kiwitcms/hu#>`_
- Updated `Portuguese, Brazilian translation <https://crowdin.com/project/kiwitcms/pt-BR#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_



Kiwi TCMS 10.2 (11 Jul 2021)
----------------------------

.. important::

    This is a small release including upgrades to 3rd party libraries
    (including security related updates), several improvements and bug fixes.

    It is the eleventh release to include contributions via our
    `open source bounty program`_!


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements & security updates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Update django from 3.2.3 to 3.2.5
- Update django-guardian from 2.3.0 to 2.4.0
- Update django-tree-queries from 0.5.1 to 0.5.2
- Update psycopg2 from 2.8.6 to 2.9.1
- Update python-gitlab from 2.7.1 to 2.9.0
- Update node_modules/marked from 2.0.3 to 2.1.3
- Update node_modules/html5sortable from 0.11.1 to 0.13.2
- Update node_modules/prismjs from 1.23.0 to 1.24.1
- Multiple select for filters on Telemetry pages. Fixes
  `Issue #1940 <https://github.com/kiwitcms/Kiwi/issues/1940>`_
  (Shantanu Verma + Alex Todorov)
- Allow editting TestCase ``setup_duration`` & ``testing_duration`` fields.
  References
  `Issue #1923 <https://github.com/kiwitcms/Kiwi/issues/1923>`_ (@APiligrim + Alex Todorov)
- Move several checks to Dashboard page instead of performing them on
  every request (Ivajlo Karabojkov)
- Fix grammatical error in documentation (Kushal Beniwal)
- Add health check for Issue Tracker configuration. Fixes
  `Issue #97 <https://github.com/kiwitcms/Kiwi/issues/97>`_
- Document API URL field for Jira integration. Closes
  `Issue #2443 <https://github.com/kiwitcms/Kiwi/issues/2443>`_


Settings
~~~~~~~~

- ``tcms.core.middleware.CheckSettingsMiddleware`` has been removed
- ``tcms.core.middleware.CheckUnappliedMigrationsMiddleware`` has been removed


API
~~~

- Method ``Version.filter()`` now returns new field called ``product__name``
- Method ``Build.filter()`` now returns new field called ``version__value``
- Methods ``Build.filter()``, ``Version.filter()`` and ``TestPlan.filter()``
  will now order their results by ``product``/``version`` and then ``id``.
- Method ``Telemetry.breakdown()`` now returns only distinct results


Bug fixes
~~~~~~~~~

- Make error messages in admin forms more legible. Fixes
  `Issue #2404 <https://github.com/kiwitcms/Kiwi/issues/2404>`_
- Large images will now fit into the available space on the screen,
  e.g. inside test case description cards. Fixes
  `Issue #2220 <https://github.com/kiwitcms/Kiwi/issues/2220>`_


Refactoring and testing
~~~~~~~~~~~~~~~~~~~~~~~

- Add automated tests for missing coverage in ``kiwi_auth.admin`` References
  `Issue #1607 <https://github.com/kiwitcms/Kiwi/issues/1607>`_ (Mariyan Garvanski)
- Apply eslint fixes (@sonyagennova + Alex Todorov)
- Refactor ``TestExecution.add_link`` method to use ModelForm and extend tests. Closes
  `Issue #1327 <https://github.com/kiwitcms/Kiwi/issues/1327>`_ (Rosen Sasov + Alex Todorov)
- Use context manager when opening files to make pylint happier
- Simplify 2 UI buttons on TestRun page
- Enable ``doc8`` for README and CHANGELOG and fix formatting errors


Translations
~~~~~~~~~~~~

- Updated `Czech translation <https://crowdin.com/project/kiwitcms/cs#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `German translation <https://crowdin.com/project/kiwitcms/de#>`_
- Updated `Hungarian translation <https://crowdin.com/project/kiwitcms/hu#>`_
- Updated `Japanese translation <https://crowdin.com/project/kiwitcms/ja#>`_
- Updated `Polish translation <https://crowdin.com/project/kiwitcms/pl#>`_
- Updated `Russian translation <https://crowdin.com/project/kiwitcms/ru#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_



Kiwi TCMS 10.1 (18 May 2021)
----------------------------

.. important::

    This release includes many improvements & security updates, database changes,
    new and updated API methods, bug fixes, translation updates, new tests and
    internal refactoring.

    It is the tenth release to include contributions via our
    `open source bounty program`_ and collaboration with Major League Hacking!

    This is the second release after Kiwi TCMS reached 400K pulls
    on Docker Hub!


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements & security updates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Upgrade from Python 3.6 to Python 3.8 inside the container
- Upgrade Django from 3.1.7 to 3.2.3
- Upgrade django-attachments from 1.8 to 1.9.1
- Upgrade django-contrib-comments from 2.0.0 to 2.1.0
- Upgrade django-extensions from 3.1.1 to 3.1.3
- Upgrade django-grappelli from 2.14.3 to 2.15.1
- Upgrade django-simple-history from 2.12.0 to 3.0.0
- Upgrade django-tree-queries from 0.4.3 to 0.5.1
- Upgrade jira from 2.0.0 to 3.0.1
- Upgrade pygments from 2.8.0 to 2.9.0
- Upgrade python-gitlab from 2.6.0 to 2.7.1
- Upgrade node_modules/html5sortable from 0.10.0 to 0.11.1
- Upgrade node_modules/marked from 2.0.1 to 2.0.3
- Timestamp fields added to all TestRun pages. Closes
  `Issue #1928 <https://github.com/kiwitcms/Kiwi/issues/1928>`_ (Andreea Moraru)
- Don't set ``TestRun.start_date`` automatically. Fixes
  `Issue #2323 <https://github.com/kiwitcms/Kiwi/issues/2323>`_ (Andreea Moraru)
- Web based database initialization for new installations. Closes
  `Issue #1698 <https://github.com/kiwitcms/Kiwi/issues/1698>`_ (Ivajlo Karabojkov)
- Automatically active the first registered user via web UI
- Rearrange layout of before and after fields on search pages
- Allow TestRun creation from navigation menu. Fixes
  `Issue #2281 <https://github.com/kiwitcms/Kiwi/issues/2281>`_
- Document hardware specs & performance baseline results. Refs
  `Issue #721 <https://github.com/kiwitcms/Kiwi/issues/721>`_
- Document performance for ``TestCase.filter``/``TestRun.filter`` methods.
  Closes
  `Issue #1173 <https://github.com/kiwitcms/Kiwi/issues/1173>`_
- Update documentation around ``docker-compose.yml`` and the extra script files
  that it needs
- Document some useful management commands
- Clarify ``set_domain`` command. Closes
  `Issue #2375 <https://github.com/kiwitcms/Kiwi/issues/2375>`_


Settings
~~~~~~~~

- Change ``TEMP_DIR`` to ``/var/tmp`` which affects the location in which
  intermadiate files coming from migrations are saved. If ``/var/tmp`` doesn't
  exist the fallback is ``/tmp`` which on modern Linux distributions is
  ephemeral
- Add ``DEFAULT_AUTO_FIELD`` to hard-code expected behavior and prevent
  unwanted changes introduced by future versions of Django


Database
~~~~~~~~

- Add new fields to ``TestCase`` - ``setup_duration``, ``testing_duration`` and
  a calculatable ``expected_duration`` attribute (Angelina)
- Remove unused ``TestRun.product_version`` field


API
~~~

- Method ``TestRun.filter()`` return value changes field names:

  - ``product_version`` -> ``plan__product_version``
  - ``product_version__value`` -> ``plan__product_version__value``

  .. warning::

      You will need to adjust your API scripts if using these fields!

- Method ``Component.filter()`` will return only distinct results
- New method ``KiwiTCMS.version()``


Bug fixes
~~~~~~~~~

- Remove links and icons from TestRun print styling. Fixes
  `Issue #2263 <https://github.com/kiwitcms/Kiwi/issues/2263>`_ and
  `Issue #2264 <https://github.com/kiwitcms/Kiwi/issues/2264>`_ (Gagan Deep)
- Emails notifications are now sent into server language. Fixes
  `Issue #1589 <https://github.com/kiwitcms/Kiwi/issues/1589>`_ (Kapil Bansal)
- Fix compatibility bug for "advanced search & add" popup windows and latest Chrome
  browsers. Fixes `Issue #2100 <https://github.com/kiwitcms/Kiwi/issues/2100>`_
- Redirect TestPlan Admin "Add" to the correct URL
- Fix wrong TestExecution field names in queryset & HTML template. Refs
  `Issue #1924 <https://github.com/kiwitcms/Kiwi/issues/1924>`_
- Add default display for ``None`` fields in Test Case page


Refactoring & testing
~~~~~~~~~~~~~~~~~~~~~

- Add test automation for ``TestExecution.actual_duration``. Refs
  `Issue #1924 <https://github.com/kiwitcms/Kiwi/issues/1924>`_ (@APiligrim)
- Add test automation for ``TestCase.expected_duration``. Refs
  `Issue #1923 <https://github.com/kiwitcms/Kiwi/issues/1923>`_ (@APiligrim)
- Add test automation for ``ReadOnlyHistoryAdmin``. Fixes
  `Issue #1604 <https://github.com/kiwitcms/Kiwi/issues/1604>`_ (Kapil Bansal)
- Add ``similar-string`` checker to ``kiwi_lint``. Fixes
  `Issue #1126 <https://github.com/kiwitcms/Kiwi/issues/1126>`_ (@17sushmita)
- Resolve or silence the remaining outstanding pylint issues. Closes
  `Issue #171 <https://github.com/kiwitcms/Kiwi/issues/171>`_
- Update isort from 5.7.0 to 5.8.0
- Convert forms to ``ModelForm``
- Remove unused method parameters
- Remove unused ``string_to_list()``. Closes
  `Issue #340 <https://github.com/kiwitcms/Kiwi/issues/340>`_
- Simplify method used for progressbar in dashboard which also
  reduces the total number of SQL queries
- Use existing functions, remove duplication
- Remove unnecessary calls & definition of ``loadInitialTestPlans()`` in
  Telemetry pages


Translations
~~~~~~~~~~~~

- Updated `Chinese Simplified translation <https://crowdin.com/project/kiwitcms/zh-CN#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Hungarian translation <https://crowdin.com/project/kiwitcms/hu#>`_
- Updated `Italian translation <https://crowdin.com/project/kiwitcms/it#>`_
- Updated `Japanese translation <https://crowdin.com/project/kiwitcms/ja#>`_
- Updated `Polish translation <https://crowdin.com/project/kiwitcms/pl#>`_
- Updated `Portuguese, Brazilian translation <https://crowdin.com/project/kiwitcms/pt-BR#>`_
- Updated `Romanian translation <https://crowdin.com/project/kiwitcms/ro#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_
- Updated `Spanish translation <https://crowdin.com/project/kiwitcms/es-ES#>`_



Kiwi TCMS 10.0 (02 March 2021)
------------------------------

.. important::

    This is a major release which includes backwards incompatible API changes,
    new database fields, improvements, bug fixes, translation updates,
    new tests and internal refactoring.
    It is the ninth release to include contributions via our
    `open source bounty program`_.

    This is the first release after Kiwi TCMS reached 400K pulls
    on Docker Hub!


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Security
~~~~~~~~

- Update node_modules/marked from 1.2.7 to 2.0.1. Also fixes
  `SNYK-JS-MARKED-1070800 <https://snyk.io/vuln/SNYK-JS-MARKED-1070800>`_
- Update django from 3.1.5 to 3.1.7 for CVE-2021-3281 and CVE-2021-23336


Improvements
~~~~~~~~~~~~

- Update bleach from 3.2.1 to 3.3.0
- Update django-colorfield from 0.3.2 to 0.4.1
- Update django-extensions from 3.1.0 to 3.1.1
- Update markdown from 3.3.3 to 3.3.4
- Update pygments from 2.7.4 to 2.8.0
- Update python-gitlab from 2.5.0 to 2.6.0
- Change ON/OFF button messages (Krum Petkov)
- Automatically set test run to finished/not-finished depending on
  the state of all executions. Closes
  `Issue #441 <https://github.com/kiwitcms/Kiwi/issues/441>`_
- Allow assigning users from group admin page. Fixes
  `Issue #1844 <https://github.com/kiwitcms/Kiwi/issues/1844>`_
- Improve documentation around setting up devel environment


Database
~~~~~~~~

- Add ``TestRun.planned_start`` and ``TestRun.planned_stop`` fields. Refs
  `Issue #1928 <https://github.com/kiwitcms/Kiwi/issues/1928>`_ (Andreea Moraru)
- Add ``TestExecution.start_date`` field. Refs
  `Issue #1924 <https://github.com/kiwitcms/Kiwi/issues/1924>`_ (Anastasiya Uraleva)
- Rename field ``TestExecution.close_date`` to ``TestExecution.stop_date``
  (Anastasiya Uraleva)


API
~~~

.. warning::

    This release changes how Kiwi TCMS serializes API results and thus
    introduces multiple backwards incompatible changes.

.. important::

    All ``.filter()`` methods now return distinct records!

- New method ``PlanType.create()``
- Method ``TestCase.add_component()`` now returns a serialized ``Component``
  instead of a serialized ``TestCase``. Refs
  `Issue #2145 <https://github.com/kiwitcms/Kiwi/issues/2145>`_
- Methods ``Product.filter()``, ``Product.create()`` and ``Product.update()``:

  - change input parameter ``classification_id`` to ``classification`` -
    type int
  - change result field ``classification_id`` to ``classification`` - type int
- Method ``Category.filter()`` changes result field
  ``product_id`` to ``product`` - type int
- Methods ``Component.filter()``, ``Component.create()`` and
  ``Component.update()``:

  - change input parameter ``product_id`` to ``product`` - type int
  - change input parameter ``initial_owner_id`` to ``initial_owner`` - type int
  - change input parameter ``initial_qa_contact_id`` to
    ``initial_qa_contact`` - type int
  - change result field ``product_id`` to ``product`` - type int
  - change result field ``initial_owner_id`` to ``initial_owner`` - type int
  - change result field ``initial_qa_contact_id`` to ``initial_qa_contact`` -
    type int
  - adds result field ``cases`` - type int - a TestCase ID if this component is
    attached to a test case
- Methods ``Version.filter()`` and ``Version.create()``:

  - change input parameter ``product_id`` to ``product`` - type int
  - change result field ``product_id`` to ``product`` - type int
- Method ``Tag.filter()`` now returns additional fields:
  ``bugs``, ``case``, ``plan`` and ``run`` which causes existing queries to
  return similar records attached to different parent objects. Consumers of
  these results should be updated
- Methods ``TestPlan.filter()``, ``TestPlan.create()`` and
  ``TestPlan.update()``:

  - change input parameter ``author_id`` to ``author`` - type int
  - change input parameter ``parent_id`` to ``parent`` - type int
  - change input parameter ``product_id`` to ``product`` - type int
  - change input parameter ``product_version_id`` to ``product_version`` -
    type int
  - change input parameter ``type_id`` to ``type`` - type int
  - change result field ``author_id`` to ``author`` - type int
  - change result field ``parent_id`` to ``parent`` - type int
  - change result field ``product_id`` to ``product`` - type int
  - change result field ``product_version_id`` to ``product_version`` -
    type int
  - change result field ``type_id`` to ``type`` - type int
  - remove result fields ``cases``, ``tag``, ``default_product_version``
- Method ``TestPlan.filter()``
  adds result fields ``product_version__value``, ``product__name``,
  ``author__username`` and ``type__name``
- Methods ``TestRun.filter()``, ``TestRun.create()`` and ``TestRun.update()``:

  - change result field ``build_id`` to ``build`` - type int
  - change result field ``default_tester_id`` to ``default_tester`` - type int
  - change result field ``manager_id`` to ``manager`` - type int
  - change result field ``plan_id`` to ``plan`` - type int
  - change result field ``product_version_id`` to ``product_version`` -
    type int
  - remove result fields ``cc``, ``tag``
- Method ``TestRun.filter()`` adds result fields ``product_version__value``,
  ``plan__product``, ``plan__name``, ``build__name``, ``manager__username`` and
  ``default_tester__username``
- Methods ``TestExecution.filter()`` and ``TestExecution.update()``:

  - change input parameter ``assigee_id`` to ``assignee`` - type int
  - change input parameter ``build_id`` to ``build`` - type int
  - change input parameter ``case_id`` to ``case`` - type int
  - change input parameter ``run_id`` to ``run`` - type int
  - change input parameter ``status_id`` to ``status`` - type int
  - change input parameter ``tested_by_id`` to ``tested_by`` - type int
  - change result field ``assigee_id`` to ``assignee`` - type int
  - change result field ``build_id`` to ``build`` - type int
  - change result field ``case_id`` to ``case`` - type int
  - change result field ``run_id`` to ``run`` - type int
  - change result field ``status_id`` to ``status`` - type int
  - change result field ``tested_by_id`` to ``tested_by`` - type int
- Method ``TestExecution.filter()`` adds result fields ``assignee__username``,
  ``tested_by__username``, ``case__summary``, ``build__name`` and
  ``status__name``
- Method ``TestExecution.get_links()`` change result field
  ``execution_id`` to ``execution`` - type int
- Method ``TestRun.add_case()`` changes result field names similarly to
  ``TestExecution.filter()`` method
- Methods ``TestCase.filter()``, ``TestCase.create()`` and
  ``TestCase.update()``:

  - change input parameter ``author_id`` to ``author`` - type int
  - change input parameter ``case_status_id`` to ``case_status`` - type int
  - change input parameter ``category_id`` to ``category`` - type int
  - change input parameter ``default_tester_id`` to ``default_tester`` -
    type int
  - change input parameter ``priority_id`` to ``priority`` - type int
  - change input parameter ``reviewer_id`` to ``reviewer`` - type int
  - change result field ``author_id`` to ``author`` - type int
  - change result field ``case_status_id`` to ``case_status`` - type int
  - change result field ``category_id`` to ``category`` - type int
  - change result field ``default_tester_id`` to ``default_tester`` - type int
  - change result field ``priority_id`` to ``priority`` - type int
  - change result field ``reviewer_id`` to ``reviewer`` - type int
  - remove result fields ``component``, ``plan``, ``tag``
- Method ``TestCase.filter()`` adds result fields ``case_status__name``,
  ``category__name``, ``priority__value``, ``author__username``,
  ``default_tester__username`` and ``reviewer__username``
- Methods ``TestRun.get_cases()`` and ``TestPlan.add_case()`` change
  result field names similarly to ``TestCase.filter()`` method


Bug fixes
~~~~~~~~~

- Fix removing a component from a test case immediately after it has been added. Fixes
  `Issue #2145 <https://github.com/kiwitcms/Kiwi/issues/2145>`_ (Gagan Deep)
- Fix broken object navigation in navbar. Fixes
  `Issue #991 <https://github.com/kiwitcms/Kiwi/issues/991>`_
- Refactor search pages rendering to speed it up. Closes
  `Issue #1014 <https://github.com/kiwitcms/Kiwi/issues/1014>`_


Refactoring & testing
~~~~~~~~~~~~~~~~~~~~~

- Update tests for ``TestRun.create()`` API method. Refs
  `Issue #1928 <https://github.com/kiwitcms/Kiwi/issues/1928>`_ (Andreea Moraru)
- Add automation tests. Closes
  `Issue #1618 <https://github.com/kiwitcms/Kiwi/issues/1618>`_ (Mariyan Garvanski)
- Add additional automation tests for ``tcms.management.admin``. Closes
  `Issue #1610 <https://github.com/kiwitcms/Kiwi/issues/1610>`_ (Gagan Deep)
- Add additional automation tests for ``tcms.testcases.views.EditTestCaseView``. Closes
  `Issue #1615 <https://github.com/kiwitcms/Kiwi/issues/1615>`_ (Gagan Deep)
- Add additional automation tests for ``tcms.kiwi_auth.forms``. Closes
  `Issue #1609 <https://github.com/kiwitcms/Kiwi/issues/1609>`_ (Kapil Bansal)
- Change location of included HTML templates (Alexander Tsvetanov, Krum Petkov)
- Erase unused view & templates (Alexander Tsvetanov)
- Enable eslint. Closes
  `Issue #1281 <https://github.com/kiwitcms/Kiwi/issues/1281>`_
- Change how beakerlib test framework is installed to avoid problems
  during integration tests
- Better inspection of beakerlib test results to avoid false positive results


Translations
~~~~~~~~~~~~

- Updated `Bulgarian translation <https://crowdin.com/project/kiwitcms/bg#>`_
- Updated `German translation <https://crowdin.com/project/kiwitcms/de#>`_
- Updated `Hungarian translation <https://crowdin.com/project/kiwitcms/hu#>`_
- Updated `Polish translation <https://crowdin.com/project/kiwitcms/pl#>`_



Kiwi TCMS 9.0.1 (14 Jan 2021)
-----------------------------

Bug fixes
~~~~~~~~~

- Update name of query parameter. Fixes
  `Issue #2196 <https://github.com/kiwitcms/Kiwi/issues/2196>`_


Kiwi TCMS 9.0 (12 Jan 2021)
---------------------------

.. important::

    This is a major release which includes backwards incompatible
    database and API changes, improvements, bug fixes, translation updates,
    new tests and internal refactoring.
    It is the eight release to include contributions via our
    `open source bounty program`_.

    This is the third release after `Kiwi TCMS reached 200K pulls
    <https://kiwitcms.org/blog/kiwi-tcms-team/2020/10/26/kiwi-tcms-celebrates-200k-downloads/>`_
    on Docker Hub!


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update django from 3.1.4 to 3.1.5
- Update django-contrib-comments from 1.9.2 to 2.0.0
- Update pygithub from 1.53 to 1.54.1
- Update pygments from 2.7.3 to 2.7.4
- Update mysqlclient from 2.0.1 to 2.0.3
- Update node_modules/prismjs from 1.22.0 to 1.23.0
- Update node_modules/marked from 1.2.5 to 1.2.7
- Implement 'Select all' for TestCase Search page. Resolves
  `Issue #2103 <https://github.com/kiwitcms/Kiwi/issues/2103>`_ (Bryan Mutai)
- Change ON/OFF button messages for several buttons (Krum Petkov)
- Remove ``delete_selected`` action from admin pages
- Show active test runs in TestPlan page
- Hide irrelevant Version & Build selectors for Testing breakdown telemetry
- Allow ``running`` to be passed as URL query param to TestRun Search page


Settings
~~~~~~~~

- Remove unused ``kiwi.rpc`` log handler from ``LOGGING`` setting


Database
~~~~~~~~

.. warning::

    Contains backwards incompatible changes.

- Replace ``Build.product`` with ``Build.version``. Closes
  `Issue #246 <https://github.com/kiwitcms/Kiwi/issues/246>`_. Build objects
  are now associated with Version objects, not with Product objects!

  .. warning::

     After migration existing builds will point to the "unspecified" version!
     If you want your telemetry to be accurate you will have to update these
     objects manually and point them to the appropriate version value!

- Rename related_name for TestExecution model: ``case_run`` -> ``executions``
- Rename related_name for TestCase model: ``case`` -> ``cases``


API
~~~

.. warning::

    Contains backwards incompatible changes.

- Methods ``Build.filter``, ``Build.create`` and ``Build.update`` replace the
  ``product`` field with a ``version`` field


Bug fixes
~~~~~~~~~

- Display raw Markdown text before rendering to fix a bug where anymous users
  don't see any text on the screen even if they are allowed to view an object


Refactoring & testing
~~~~~~~~~~~~~~~~~~~~~

- Add tests for ``tcms.core.middleware``. Fixes
  `Issue #1605 <https://github.com/kiwitcms/Kiwi/issues/1605>`_ (Gagan Deep)
- Add tests for ``tcms.handlers``. Fixes
  `Issue #1611 <https://github.com/kiwitcms/Kiwi/issues/1611>`_ (Gagan Deep)
- Add tests for ``tcms.kiwi_auth.views``. Fixes
  `Issue #1608 <https://github.com/kiwitcms/Kiwi/issues/1608>`_
  (Abhishek Chaurasia)
- Update pip during bugtracker integration tests to fix dependency issues
- Reformat all files with black and isort. Closes
  `Issue #1193 <https://github.com/kiwitcms/Kiwi/issues/1193>`_
- Refactor ``TestExecution.get_bugs()`` to use ``TestExecution.links()``
- Add return statement for invalid form to make pylint happy
- Make ``Bug.assignee`` field a ``UserField``
- Replace deprecated ``ugettext_lazy`` with ``gettext_lazy``
- Fixes for Azure Boards integration tests
- Remove ``CsrfDisableMiddleware``. Closes
  `Issue #297 <https://github.com/kiwitcms/Kiwi/issues/297>`_
- Remove unused methods & left-over views


Translations
~~~~~~~~~~~~

- Updated `Catalan translation <https://crowdin.com/project/kiwitcms/ca#>`_
- Updated `Chinese Simplified translation <https://crowdin.com/project/kiwitcms/zh-CN#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Hungarian translation <https://crowdin.com/project/kiwitcms/hu#>`_
- Updated `Japanese translation <https://crowdin.com/project/kiwitcms/ja#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_



Kiwi TCMS 8.9 (07 Dec 2020)
---------------------------

.. important::

    This release includes many improvements,
    API changes, bug fixes, translation updates,
    new tests and internal refactoring.
    It is the seventh release to include contributions via our
    `open source bounty program`_.

    This is the second release after `Kiwi TCMS reached 200K pulls
    <https://kiwitcms.org/blog/kiwi-tcms-team/2020/10/26/kiwi-tcms-celebrates-200k-downloads/>`_
    on Docker Hub!


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update django from 3.1.3 to 3.1.4
- Update django-extensions from 3.0.9 to 3.1.0
- Update django-grappelli from 2.14.2 to 2.14.3
- Update pygments from 2.7.2 to 2.7.3
- Update python-bugzilla from 3.0.1 to 3.0.2
- Update node_modules/marked from 1.2.3 to 1.2.5
- Update node_modules/html5sortable from 0.9.18 to 0.10.0
- New ``manage.py initial_setup`` command for one-stop initial setup
  (Ivajlo Karabojkov)
- Bug tracker integration with BitBucket (bitbucket.org). Fixes
  `Issue #1916 <https://github.com/kiwitcms/Kiwi/issues/1916>`_ (@cmbahadir)
- Complete redesign and refactoring of Test Run page:

  - Closes
    `Issue #189 <https://github.com/kiwitcms/Kiwi/issues/189>`_,
    `Issue #241 <https://github.com/kiwitcms/Kiwi/issues/241>`_,
    `Issue #212 <https://github.com/kiwitcms/Kiwi/issues/212>`_,
    `Issue #431 <https://github.com/kiwitcms/Kiwi/issues/431>`_,
    `Issue #1382 <https://github.com/kiwitcms/Kiwi/issues/1382>`_
  - Add filter by component & tag. Closes
    `Issue #833 <https://github.com/kiwitcms/Kiwi/issues/833>`_
  - Don't limit the user to test cases from the parent test plan like before.
    Testers can add any test case for execution inside a test run,
    even mix & match test cases between products. Fixes
    `Issue #1934 <https://github.com/kiwitcms/Kiwi/issues/1934>`_
  - Add attachments to Test Run page. Fixes
    `Issue #872 <https://github.com/kiwitcms/Kiwi/issues/872>`_
  - Refresh execution row after reporting a bug. Closes
    `Issue #479 <https://github.com/kiwitcms/Kiwi/issues/479>`_
- ``TestCaseStatus`` can now be customized. Fixes
  `Issue #1932 <https://github.com/kiwitcms/Kiwi/issues/1932>`_
- Update documantation & screenshots


Settings
~~~~~~~~

- Setting ``ANONYMOUS_USER_NAME`` is now explicitly defined due to upstream bug
  in django-guardian (Abhishek Chaurasia)


Database
~~~~~~~~

- New migrations for customizeable ``TestCaseStatus``


API
~~~

- Add ``TestExecution.history()`` meethod
- Add ``TestCase.history()`` method
- Add ``TestRun.add_cc()`` method
- Add ``TestRun.remove_cc()`` method
- Method ``TestExecution.update()`` will use build from parent test run if a
  ``build`` field isn't explicitly specified in the arguments
- Update method ``TestRun.add_case()``

  - will return existing TestExecution if available
  - will raise if test case status is not confirmed
  - will always create new test executions with the highest sortkey


Bug fixes
~~~~~~~~~

- Fixed miscellaneous bugs in ``tcms.rpc.testcase`` (Gagan Deep)
- Disable name change in admin for the default groups. Fixes
  `Issue #1313 <https://github.com/kiwitcms/Kiwi/issues/1313>`_


Refactoring & testing
~~~~~~~~~~~~~~~~~~~~~

- Add automated tests for ``tcms.core.views.server_error``. Fixes
  `Issue #1606 <https://github.com/kiwitcms/Kiwi/issues/1606>`_
  (Abhishek Chaurasia)
- Add automated tests for ``tcms.rpc.api.auth``. Fixes
  `Issue #1620 <https://github.com/kiwitcms/Kiwi/issues/1620>`_
  (Abhishek Chaurasia)
- Add automated test for ``AnonymousViewBackend.has_perm`` method. Fixes
  `Issue #1905 <https://github.com/kiwitcms/Kiwi/issues/1905>`_
  (Abhishek Chaurasia)
- Add automated tests for ``tcms.core.utils.maito``. Fixes
  `Issue #1603 <https://github.com/kiwitcms/Kiwi/issues/1603>`_ (Gagan Deep)
- Add automated tests for ``tcms.utils.github``. Fixes
  `Issue #1612 <https://github.com/kiwitcms/Kiwi/issues/1612>`_ (Gagan Deep)
- Add automated tests for ``tcms.rpc.api.testscase``. Fixes
  `Issue #1623 <https://github.com/kiwitcms/Kiwi/issues/1623>`_ (Gagan Deep)
- Add automated tests for ``tcms.testcases.views.NewCaseView``. Fixes
  `Issue #1614 <https://github.com/kiwitcms/Kiwi/issues/1614>`_ (@rish07)
- Add automated tests for ``tcms.testplans.views.NewTestPlanView.`` Fixes
  `Issue #1616 <https://github.com/kiwitcms/Kiwi/issues/1616>`_ (@awalvie)
- Separate two functions one from another (Alexander Tsvetanov)
- Disable pylint checks (Alexander Tsvetanov)
- Upgrade to MySQL 8 in Travis CI
- Remove unused setup in Travis CI
- Be more robust when keeping internal state for TestPlan page


Translations
~~~~~~~~~~~~

- Updated `Bulgarian translation <https://crowdin.com/project/kiwitcms/bg#>`_
- Updated `Chinese Simplified translation <https://crowdin.com/project/kiwitcms/zh-CN#>`_
- Updated `Czech translation <https://crowdin.com/project/kiwitcms/cs#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Indonesian translation <https://crowdin.com/project/kiwitcms/id#>`_
- Updated `Japanese translation <https://crowdin.com/project/kiwitcms/ja#>`_
- Updated `Russian translation <https://crowdin.com/project/kiwitcms/ru#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_



Kiwi TCMS 8.8 (07 Nov 2020, the 200K edition)
---------------------------------------------

.. important::

    This release includes many improvements,
    API changes, bug fixes, translation updates,
    new tests and internal refactoring.
    It is the sixth release to include contributions via our
    `open source bounty program`_.

    This is also the first release after `Kiwi TCMS reached 200K pulls
    <https://kiwitcms.org/blog/kiwi-tcms-team/2020/10/26/kiwi-tcms-celebrates-200k-downloads/>`_
    on Docker Hub!


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update bleach from 3.1.5 to 3.2.1
- Update django-extensions from 3.0.8 to 3.0.9
- Update django from 3.1.1 to 3.1.3
- Update django-simple-history from 2.11.0 to 2.12.0
- Update markdown from 3.2.2 to 3.3.3
- Update pygments from 2.7.0 to 2.7.2
- Update python-bugzilla from 2.5.0 to 3.0.1
- Update node_modules/marked from 1.1.1 to 1.2.3
- Update node_modules/prismjs from 1.21.0 to 1.22.0
- Add management command ``refresh_permission``. Closes
  `Issue #1137 <https://github.com/kiwitcms/Kiwi/issues/1137>`_ (Ivajlo Karabojkov)
- Add bug tracker integration for Azure Boards. Closes
  `Issue #1979 <https://github.com/kiwitcms/Kiwi/issues/1979>`_ (@cmbahadir)
- Add autosave configuration to web editor. Closes
  `Issue #1958 <https://github.com/kiwitcms/Kiwi/issues/1958>`_ (Mfon Eti-mfon)
- Change ON/OFF button messages to Yes/No for several buttons
  (Alexander Tsvetanov)
- Add support for object-level permissions for TestCase,
  TestPlan, TestRun and Bug objects via ``django-guardian``
- Complete redesign of Test Plan page to match the rest of Kiwi TCMS:

  - modern look and feel using the PatternFly UI library
  - remove unused legacy code & HTML templates
  - closes
    `Issue #663 <https://github.com/kiwitcms/Kiwi/issues/663>`_,
    `Issue #1977 <https://github.com/kiwitcms/Kiwi/issues/1977>`_

- Enable Markdown support for strike-through text
- Always pull latest RPMs when building container images
- Update documentation and images


Settings
~~~~~~~~

- ``AUTHENTICATION_BACKENDS`` setting is now explicitly specified because of
  ``django-guardian``. Take care to include the default backends if you
  override this setting. See ``tcms/settings/common.py`` for more information.


Database
~~~~~~~~

- Add index to ``TestCase.summary`` field
- Additional migrations from ``django-guardian`` around object-level
  permissions
- New ``AnonymousUser`` record added by ``django-guardian``
- Start using ``django-tree-queries`` which improves how tree based structures
  are stored in the database.

  .. important::

    Requires PostgreSQL, sqlite3 >= 3.8.3, MariaDB >= 10.2.2 or
    MySQL >= 8.0 (if running without ``ONLY_FULL_GROUP_BY``).

  .. warning::

    Supports only trees with max. 50 levels on MySQL/MariaDB, since those databases
    do not support arrays and require us to provide a maximum length upfront.
    This means up to 50 levels of nested child-parent test plans!


API
~~~

- Method ``TestExecution.update()`` will now modify field ``close_date``
  depending on test execution status. Fixes
  `Issue #1820 <https://github.com/kiwitcms/Kiwi/issues/1820>`_
- Method ``TestCase.add_comment()`` now returns the created comment
- Method ``TestExecution.add_comment()`` now returns the created comment
- Method ``TestPlan.add_case()`` now returns the newly added test case
- Add method ``TestCase.sortkeys()``. Fixes
  `Issue #444 <https://github.com/kiwitcms/Kiwi/issues/444>`_
- Add method ``Markdown.render()``
- Add method ``TestCase.comments()``
- Add method ``TestPlan.tree()``


Bug fixes
~~~~~~~~~

- Fix url formatting. Fixes
  `Issue #1806 <https://github.com/kiwitcms/Kiwi/issues/1806>`_ (Rosen Sasov)
- When deleting TestExecutionStatus check that there will be at least 1 left
  before deleting! Closes
  `Issue #1978 <https://github.com/kiwitcms/Kiwi/issues/1978>`_
- Update typeahead definitions for test case components, tags and
  for adding test plans to test cases. Fixes
  `Issue #882 <https://github.com/kiwitcms/Kiwi/issues/882>`_
- Add option to filter by reviewer in Test Plan page. Fixes
  `Issue #564 <https://github.com/kiwitcms/Kiwi/issues/564>`_
- Pass the number of disabled test cases to HTML template when
  creating a new test run. Fixes
  `Issue #718 <https://github.com/kiwitcms/Kiwi/issues/718>`_


Refactoring & testing
~~~~~~~~~~~~~~~~~~~~~

- New linter to warn against ``GenericForeignKey`` fields in models. Closes
  `Issue #1303 <https://github.com/kiwitcms/Kiwi/issues/1303>`_ (Bryan Mutai)
- Add tests for ``assign_default_group_permissions()`` (Ivajlo Karabojkov)
- Add tests for ``TestExecutionStatusAdmin``. Refs
  `Issue #1618 <https://github.com/kiwitcms/Kiwi/issues/1618>`_ (Mariyan Garvanski)
- Add tests for ``tcms.bugs.views.Search``. Closes
  `Issue #1601 <https://github.com/kiwitcms/Kiwi/issues/1601>`_ (Mfon Eti-mfon)
- Add tests for ``tcms.rpc.api.testrun``. Closes
  `Issue #1628 <https://github.com/kiwitcms/Kiwi/issues/1628>`_ (@lcmtwn)
- Add tests for ``tcms.rpc.api.classification``. Closes
  `Issue #1621 <https://github.com/kiwitcms/Kiwi/issues/1621>`_ (Abhishek Chaurasia)
- Add tests for ``tcms.rpc.api.priority``. Closes
  `Issue #1622 <https://github.com/kiwitcms/Kiwi/issues/1622>`_ (Abhishek Chaurasia)
- Add tests for ``tcms.rpc.api.testcasestatus``. Closes
  `Issue #1624 <https://github.com/kiwitcms/Kiwi/issues/1624>`_ (Abhishek Chaurasia)
- Add tests for ``tcms.rpc.api.attachment``. Closes
  `Issue #1619 <https://github.com/kiwitcms/Kiwi/issues/1619>`_ (@awalvie)
- Add tests for ``tcms.rpc.api.testexecution.remove_comment``. Closes
  `Issue #1625 <https://github.com/kiwitcms/Kiwi/issues/1625>`_ (@awalvie)
- Add tests for ``tcms.rpc.api.testexecutionstatus``. Closes
  `Issue #1626 <https://github.com/kiwitcms/Kiwi/issues/1626>`_ (@awalvie)
- Add tests for ``TestRun.add_case_run()`` method and rename it to
  ``TestRun.create_execution()``
- ``libkrb5-dev`` is not needed anymore in CI with newer ``tcms-api``
- Use Fedora 32 to build Bugzilla docker image in CI
- Update signature for overriden class to match Django 3.1
- Move SimpleMDE initialization to simplemde_security_overide.js
- Move ``post_save.send()`` from ``bugs.views`` to ``comments.add_comment()``


Translations
~~~~~~~~~~~~

- Updated `Bulgarian translation <https://crowdin.com/project/kiwitcms/bg#>`_
- Updated `Chinese Simplified translation <https://crowdin.com/project/kiwitcms/zh-CN#>`_
- Updated `Czech translation <https://crowdin.com/project/kiwitcms/cs#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Hungarian translation <https://crowdin.com/project/kiwitcms/hu#>`_
- Updated `Italian translation <https://crowdin.com/project/kiwitcms/it#>`_
- Updated `Japanese translation <https://crowdin.com/project/kiwitcms/ja#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_



Kiwi TCMS 8.7 (16 Sep 2020)
---------------------------

**IMPORTANT:** this is a medium sized release which includes
improvements, API changes, bug fixes, translation updates and
new tests. It is the fifth release to include contributions via our
`open source bounty program`_.


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update Django from 3.0.9 to 3.1.1
- Update django-attachments from 1.6 to 1.8
- Update django-extensions from 3.0.5 to 3.0.8
- Update psycopg2 from 2.8.5 to 2.8.6
- Update pygments from 2.6.1 to 2.7.0
- Update python-gitlab from 2.4.0 to 2.5.0
- Make it possible to use reCAPTCHA during registration. If you want to enable
  this then add the following to your settings::

        if 'captcha' not in INSTALLED_APPS:
            INSTALLED_APPS.append('captcha')

            RECAPTCHA_PUBLIC_KEY = '......'
            RECAPTCHA_PRIVATE_KEY = '.....'
            RECAPTCHA_USE_SSL = True

  For more info see https://www.google.com/recaptcha/admin/
- Replace ``GlobalLoginRequiredMiddleware`` with
  ``tcms.kiwi_auth.backends.AnonymousViewBackend`` for anonymous read-only
  functionality. See section
  `Anonymous read-only access <https://kiwitcms.readthedocs.io/en/latest/configuration.html#anonymous-read-only-access>`_
  in the documentation
- Replace the ``...`` in navigation bar with a 3 cogs icon to make the
  object-level menu more visible


Settings
~~~~~~~~

- Remove setting ``PUBLIC_VIEWS``


API
~~~

- Remove ``TestCase.get_components()`` in favor of ``Component.filter()``
- ``Bug.details()`` method will now return ``{}`` instead of failing if
  it can't find an issue tracker from an URL


Bug fixes
~~~~~~~~~

- Remove documentation references to non-existing environment
- Don't fail internal calls if Kiwi TCMS bug tracker can't find a bug


Refactoring & testing
~~~~~~~~~~~~~~~~~~~~~

- Add tests for ``tcms.core.templatetags``. Closes
  `Issue #1602 <https://github.com/kiwitcms/Kiwi/issues/1602>`_ (Mariyan Garvanski)
- Add tests for ``tcms.bugs.views.Edit``. Closes
  `Issue #1599 <https://github.com/kiwitcms/Kiwi/issues/1599>`_ (Mfon Eti-mfon)
- Add tests for ``tcms.bugs.views.AddComment``. Closes
  `Issue #1600 <https://github.com/kiwitcms/Kiwi/issues/1600>`_ (Mfon Eti-mfon)
- Make paths used in migrations & settings platform aware in order to
  enable development mode on Windows (Mfon Eti-mfon)
- Add new linter checker to check for use of ``db_column`` argument in
  model field definition. Closes
  `Issue #736 <https://github.com/kiwitcms/Kiwi/issues/736>`_ (Bryan Mutai)
- Add tests for ``Bug.details`` API method
- Replace deprecated ``ifequal``/``ifnotequal`` template tags
- Adjust ``migrations_order`` for Django 3.1 compatibility
- Add ``npm audit`` check in CI
- Resolve several pylint issues


Translations
~~~~~~~~~~~~

- Updated `Bulgarian translation <https://crowdin.com/project/kiwitcms/bg#>`_
- Updated `Chinese Traditional translation <https://crowdin.com/project/kiwitcms/zh-TW#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Hungarian translation <https://crowdin.com/project/kiwitcms/hu#>`_
- Updated `Japanese translation <https://crowdin.com/project/kiwitcms/ja#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_



Kiwi TCMS 8.6 (23 Aug 2020)
---------------------------

**IMPORTANT:** this is a high severity security update which includes
improvements, database migrations, API changes, translation updates and
new tests. It is the fourth release to include contributions via our
`open source bounty program`_.


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Security
~~~~~~~~

- A high severity vulnerability which allows unprivileged data access
  via JSON-RPC endpoints has been fixed:

  - Affects all previous versions of Kiwi TCMS
  - Instances on public networks, such as Amazon EC2, are at higher risk
  - Instances on private networks are still vulnerable to anyone who can
    access the same network
  - This vulnerability has been disclosed by Michael Longmire (ShastaQA)
    and Stone Pack (ShastaQA)

- Update marked from 0.8.2 to 1.1.1 for a medium severity vulnerability, see
  `SNYK-JS-MARKED-584281 <https://snyk.io/vuln/SNYK-JS-MARKED-584281>`_


Improvements
~~~~~~~~~~~~

- Update django from 3.0.8 to 3.0.9
- Update django-attachments from 1.5 to 1.6
- Update prismjs from 1.20.0 to 1.21.0
- Update pygithub from 1.51 to 1.53
- Replace deprecated bleach-whitelist with bleach-allowlist
- Make django-extensions a production dependency because it provides
  many useful manage.py commands
- Enable syntax highlight for code blocks
- Remove file attachments when related objects are deleted
- Add image and file upload buttons to text editor. Fixes
  `Issue #977 <https://github.com/kiwitcms/Kiwi/issues/977>`_
- Require ``auth.view_user`` permission when trying to view user profiles.
  Fixes `Issue #1685 <https://github.com/kiwitcms/Kiwi/issues/1685>`_
- Multiple pages now explicitly require view permissions before displaying
  read-only information. This gives administrators a finer grained control:

  - ``/bugs/<id>/``    -> ``bugs.view_bug``
  - ``/bugs/search/``  -> ``bugs.view_bug``
  - ``/cases/search/`` -> ``testcases.view_testcase``
  - ``/case/<id>/``    -> ``testcases.view_testcase``
  - ``/plans/search/`` -> ``testplans.view_testplan``
  - ``/plan/<id>/*``   -> ``testplans.view_testplan``
  - ``/runs/search/``  -> ``testruns.view_testrun``
  - ``/runs/<id>/``    -> ``testruns.view_testrun``

  Previously these pages only required the user to be logged in


.. warning::

    The ``auth.view_user`` permission is not granted by default because the
    profile page contains personal information like names and email address, see
    :ref:`managing-permissions`.


Database
~~~~~~~~

- Migrations which manipulate data (contain ``RunPython``) can now be
  rollbacked. See ``./manage.py migrate --plan`` for the order in which
  migrations are applied (Bryan Mutai)
- Increase ``Product.name`` size from 64 to 255 characters


API
~~~

- Remove method ``TestExecution.create()`` in favor of ``TestRun.add_case()``
- Add method ``User.add_attachment()``
- Multiple API methods now explicitly require view permissions before returning
  read-only information. This is in-sync with the per-page changes
  listed above:

  - ``Bug.filter()``                   -> ``bugs.view_bug``
  - ``Bug.report()``                   -> ``testruns.view_testexecution``
  - ``Build.filter()``                 -> ``management.view_build``
  - ``Category.filter()``              -> ``testcases.view_category``
  - ``Classification.filter()``        -> ``management.view_classification``
  - ``Component.filter()``             -> ``management.view_component``
  - ``PlanType.filter()``              -> ``testplans.view_plantype``
  - ``Priority.filter()``              -> ``management.view_priority``
  - ``Product.filter()``               -> ``management.view_product``
  - ``Tag.filter()``                   -> ``management.view_tag``
  - ``TestCase.get_components()``      -> ``testcases.view_testcase``
  - ``TestCase.get_notification_cc()`` -> ``testcases.view_testcase``
  - ``TestCase.filter()``              -> ``testcases.view_testcase``
  - ``TestCaseStatus.filter()``        -> ``testcases.view_testcasestatus``
  - ``TestExecution.filter()``         -> ``testruns.view_testexecution``
  - ``TestExecution.get_links()``      -> ``linkreference.view_linkreference``
  - ``TestExecutionStatus.filter()``   -> ``testruns.view_testexecutionstatus``
  - ``TestPlan.filter()``              -> ``testplans.view_testplan``
  - ``TestRun.get_cases()``            -> ``testruns.view_testrun``
  - ``TestRun.filter()``               -> ``testruns.view_testrun``
  - ``User.filter()``                  -> ``auth.view_user``
  - ``Version.filter()``               -> ``management.view_version``


Bug fixes
~~~~~~~~~

- Update documentation to reflect that test cases cannot be rearranged from
  within a TestRun but only from a TestPlan. Fixes
  `Issue #1805 <https://github.com/kiwitcms/Kiwi/issues/1805>`_ (@Prome88)
- Incorrect code formatting for HTML <pre> tags. Closes
  `Issue #1300 <https://github.com/kiwitcms/Kiwi/issues/1300>`_
- Fix a bug with the history handler when importing objects with ID field set.
  Resolves a crash when trying to restore backup data
- Delete comments when Bug is removed


Refactoring & testing
~~~~~~~~~~~~~~~~~~~~~

- Add linter to warn about missing backwards migrations callable in ``RunPython``
  and fix all pylint offenses. Fixes
  `Issue #1774 <https://github.com/kiwitcms/Kiwi/issues/1774>`_ (Bryan Mutai)
- Teach linter to check API for ``@permissions_required``. Fixes
  `Issue #1089 <https://github.com/kiwitcms/Kiwi/issues/1089>`_
- Refactor ``NewExecutionForm`` to use ModelForm (Rosen Sasov)
- Refactor ``UpdateExecutionForm`` to use ModelForm (Rosen Sasov)
- Add tests for ``tcms.bugs.api``. Closes
  `Issue #1597 <https://github.com/kiwitcms/Kiwi/issues/1597>`_ (Mfon Eti-mfon)
- Add tests for ``tcms.bugs.views.New``. Closes
  `Issue #1598 <https://github.com/kiwitcms/Kiwi/issues/1598>`_ (Mfon Eti-mfon)
- Add tests for ``tcms.rpc.api.testplan``. Closes
  `Issue #1627 <https://github.com/kiwitcms/Kiwi/issues/1627>`_ (@lcmtwn)
- Add tests for ``percentage()`` function References
  `Issue #1602 <https://github.com/kiwitcms/Kiwi/issues/1602>`_ (Mariyan Garvanski)
- Add the ``migrations_order`` command to help test rollbacks
- Adjust code for deprecation warnings from Django 3.1
- Use Python 3 style ``super()`` without arguments
- Update login page to match our new website design


Translations
~~~~~~~~~~~~

- Updated `Chinese Simplified translation <https://crowdin.com/project/kiwitcms/zh-CN#>`_
- Updated `Czech translation <https://crowdin.com/project/kiwitcms/cs#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `German translation <https://crowdin.com/project/kiwitcms/de#>`_
- Updated `Hungarian translation <https://crowdin.com/project/kiwitcms/hu#>`_
- Updated `Japanese translation <https://crowdin.com/project/kiwitcms/ja#>`_
- Updated `Portuguese, Brazilian translation <https://crowdin.com/project/kiwitcms/pt-BR#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_



Kiwi TCMS 8.5 (10 Jul 2020)
---------------------------

**IMPORTANT:** this is a medium sized release which includes many improvements,
database migrations, translation updates and new tests.
It is the third release to include contributions via our
`open source bounty program`_.


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update django from 3.0.7 to 3.0.8
- Update django-colorfield from 0.3.0 to 0.3.2
- Update django-modern-rpc from 0.12.0 to 0.12.1
- Update django-simple-history from 2.10.0 to 2.11.0
- Update mysqlclient from 1.4.6 to 2.0.1
- Update python-gitlab from 2.2.0 to 2.4.0
- Update python-bugzilla from 2.3.0 to 2.5.0
- Add middleware to warn for unapplied migrations. Fixes
  `Issue #1696 <https://github.com/kiwitcms/Kiwi/issues/1696>`_ (Bryan Mutai)
- Add "insert table" button to SimpleMDE toolbar. References
  `Issue #1531 <https://github.com/kiwitcms/Kiwi/issues/1531>`_ (Bryan Mutai)
- Implement
  `kiwitcms-django-plugin <https://kiwitcms.org/blog/kiwi-tcms-team/2020/06/30/django-plugin-for-kiwi-tcms/>`_.
  Resolves `Issue #693 <https://github.com/kiwitcms/Kiwi/issues/693>`_
  (Bryan Mutai)
- Add missing permission check for ``TestExecution.add_link()`` API method
  (Rosen Sasov)
- Add missing permission check for ``TestExecution.remove_link()`` API method
  (Rosen Sasov)
- Admin interface will now appear translated
- Propagate server side API errors to the browser. Closes
  `Issue #625 <https://github.com/kiwitcms/Kiwi/issues/625>`_,
  `Issue #1333 <https://github.com/kiwitcms/Kiwi/issues/1333>`_
- Improvements for Status Matrix telemetry page:

  - Make the horizontal scroll bar at the bottom always visible
  - Make the header row always visible
  - Add button to show columns in reverse. Fixes
    `Issue #1682 <https://github.com/kiwitcms/Kiwi/issues/1682>`_
  - Make it possible to display TestExecutions from child TestPlans. Fixes
    `Issue #1683 <https://github.com/kiwitcms/Kiwi/issues/1683>`_


Database
~~~~~~~~

- Update existing Bug tracker records to match the changes introduced with
  the new ``EXTERNAL_BUG_TRACKERS`` setting


Settings
~~~~~~~~

- Add ``EXTERNAL_BUG_TRACKERS`` setting which is a list of dotted class paths
  representing external bug tracker integrations. Plugins and Kiwi TCMS admins
  can now more easily include customized integrations


Refactoring & testing
~~~~~~~~~~~~~~~~~~~~~

- Add new linter to check for label arguments in form field classes. Fixes
  `Issue #738 <https://github.com/kiwitcms/Kiwi/issues/738>`_ (Bryan Mutai)
- Add new linter to check if all forms inherit from ``ModelForm``. Fixes
  `Issue #1384 <https://github.com/kiwitcms/Kiwi/issues/1384>`_ (Bryan Mutai)
- Enable pylint plugin ``pylint.extensions.docparams`` and resolve errors. Fixes
  `Issue #1192 <https://github.com/kiwitcms/Kiwi/issues/1192>`_ (Bryan Mutai)
- Migrate 'test-for-missing-migrations' from Travis CI to GitHub workflow. Fixes
  `Issue #1553 <https://github.com/kiwitcms/Kiwi/issues/1553>`_ (Bryan Mutai)
- Add tests for ``tcms.bugs.api.add_tag()``. References
  `Issue #1597 <https://github.com/kiwitcms/Kiwi/issues/1597>`_ (Mfon Eti-mfon)
- Add tests for ``tcms.bugs.api.remove_tag()``. References
  `Issue #1597 <https://github.com/kiwitcms/Kiwi/issues/1597>`_ (Mfon Eti-mfon)
- Add test for ``tcms.testplans.views.Edit``. References
  `Issue #1617 <https://github.com/kiwitcms/Kiwi/issues/1617>`_ (@cmbahadir)
- Add tests for ``markdown2html()``. Fixes
  `Issue #1659 <https://github.com/kiwitcms/Kiwi/issues/1659>`_ (Mariyan Garvanski)
- Add test for Cyrillic support with MariaDB. References
  `Issue #1770 <https://github.com/kiwitcms/Kiwi/issues/1770>`_


Translations
~~~~~~~~~~~~

- Updated `Chinese Simplified translation <https://crowdin.com/project/kiwitcms/zh-CN#>`_
- Updated `Chinese Traditional translation <https://crowdin.com/project/kiwitcms/zh-TW#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Hungarian translation <https://crowdin.com/project/kiwitcms/hu#>`_
- Updated `Indonesian translation <https://crowdin.com/project/kiwitcms/id#>`_
- Updated `Japanese translation <https://crowdin.com/project/kiwitcms/ja#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_
- Updated `Swahili translation <https://crowdin.com/project/kiwitcms/sw#>`_



Kiwi TCMS 8.4 (03 June 2020)
----------------------------

**IMPORTANT:** this is a medium sized release which includes
minor security fixes, many improvements & bug-fixes and translations
in several new languages. It is the second release to include
contributions via our `open source bounty program`_.

.. important::

    Last month we've also reached an important milestone - 100K+ pulls on Docker Hub !!!

Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update Django from 3.0.5 to 3.0.7 -
  `security update <https://docs.djangoproject.com/en/3.0/releases/3.0.7/>`_
  for functionality not used by Kiwi TCMS
- Update bleach from 3.1.4 to 3.1.5
- Update django-grappelli from 2.14.1 to 2.14.2
- Update django-simple-history from 2.9.0 to 2.10.0
- Update markdown from 3.2.1 to 3.2.2
- Update pygithub from 1.50 to 1.51
- Update python-redmine from 2.2.1 to 2.3.0
- Update patternfly from 3.59.4 to 3.59.5
- Add ``manage.py set_domain`` command to change Kiwi TCMS domain. Fixes
  `Issue #971 <https://github.com/kiwitcms/Kiwi/issues/971>`_ (Ivajlo Karabojkov)
- GitHub bug details now works for private issues
- Gitlab bug details now works for private issues
- JIRA bug details now works for private issues
- Redmine bug details now works for private issues
- New feature: 1-click bug report for Bugzilla
- New feature: 1-click bug report for Gitlab
- New feature: 1-click bug report for JIRA
- New feature: 1-click bug report for Redmine
- Reverting to older historical version via Admin panel now redirects
  to object which was reverted. Fixes
  `Issue #1074 <https://github.com/kiwitcms/Kiwi/issues/1074>`_
- Documentation updates

.. important::

    Starting from v8.4 all supported bug trackers now feature
    1-click bug report integration!

.. note::

    Some external bug trackers like Bugzilla & JIRA provide more
    flexibility over which fields are required for a new bug report.
    The current functionality should work for vanilla installations and would
    fall back to manual bug reporting if it can't create a new bug
    automatically!


Database
~~~~~~~~

- Force creation of missing permissions for m2m fields from the
  ``tcms.bugs`` app:

  - ``bugs.add_bug_tags``
  - ``bugs.change_bug_tags``
  - ``bugs.delete_bug_tags``
  - ``bugs.view_bug_tags``
  - ``bugs.add_bug_executions``
  - ``bugs.change_bug_execution``
  - ``bugs.delete_bug_execution``
  - ``bugs.view_bug_executions``

.. warning::

    TCMS admins of existing installations will have to assign these by hand
    to users/groups who will be allowed to change tags on bugs!


Settings
~~~~~~~~

- Define the ``KIWI_DISABLE_BUGTRACKER=yes`` environment variable if you wish
  to disable the internal bug tracker. Closes
  `Issue #1370 <https://github.com/kiwitcms/Kiwi/issues/1370>`_


Bug fixes
~~~~~~~~~

- Workaround missing MariaDB CHARSET/COLLATION support, see our
  ``docker-compose.yml``. Fixes
  `Issue #1700 <https://github.com/kiwitcms/Kiwi/issues/1700>`_
- Install missing ``/usr/bin/mysql`` in container
- Warning message for unconfigured Kiwi TCMS domain does not show HTML tags in
  Admin anymore. Fixes
  `Issue #964 <https://github.com/kiwitcms/Kiwi/issues/964>`_
- Unescape the ``&amp;`` string when trying to open new windows after
  clicking the 'Report bug' button in TestExecution. Fixes
  `Issue #1533 <https://github.com/kiwitcms/Kiwi/issues/1533>`_
- Try harder to restore the original navigation menu instead of
  leaving bogus menu items. Fixes
  `Issue #991 <https://github.com/kiwitcms/Kiwi/issues/991>`_
- Robot Framework plugin is now GA. Close
  `Issue #984 <https://github.com/kiwitcms/Kiwi/issues/984>`_
- Add LinkReference to TestExecution after creating bug via 1-click.
  The UI still needs to be refreshed which will be implemented together
  with the redesign of the TestRun page
- Update documented signature for API method ``TestCase.add_component`` to
  match current behavior, see https://stackoverflow.com/questions/61648405/


Refactoring & testing
~~~~~~~~~~~~~~~~~~~~~

- Migrate ``check-docs-source-in-git`` to GitHub workflows. Fixes
  `Issue #1552 <https://github.com/kiwitcms/Kiwi/issues/1552>`_ (@Prome88)
- Migrate ``build-for-pypi`` to GitHub workflows. Fixes
  `Issue #1554 <https://github.com/kiwitcms/Kiwi/issues/1554>`_ (@lcmtwn)
- Add tests for ``TestCaseAdmin`` (Mariyan Garvanski)
- Add tests for ``BugAdmin``. Fixes
  `Issue #1596 <https://github.com/kiwitcms/Kiwi/issues/1596>`_ (Mariyan Garvanski)
- Omit ``utils/test`` from coverage reports. Fixes
  `Issue #1631 <https://github.com/kiwitcms/Kiwi/issues/1631>`_ (@cmbahadir)
- Omit ``tcms/tests`` from coverage reports. Fixes
  `Issue #1630 <https://github.com/kiwitcms/Kiwi/issues/1630>`_ (@cmbahadir)
- Add tests for ``tcms.core.forms.fields`` - Fixes
  `Issue #1629 <https://github.com/kiwitcms/Kiwi/issues/1629>`_ (@cmbahadir)
- Add tests for ``TestExecution.update()`` for ``case_text_version`` field
  (Rosen Sasov)
- Refactor bulk-update methods in TestRun page to use JSON-RPC. Fixes
  `Issue #1063 <https://github.com/kiwitcms/Kiwi/issues/1063>`_ (Rosen Sasov)
- Start using ``_change_reason`` instead of ``changeReason`` field in
  django-simple-history
- Remove unused ``StripURLField`` & ``Version.string_to_id()``
- Refactoring around TestCase and TestPlan cloning methods
- Start testing with the internal bug tracker disabled
- Start testing with all supported external bug trackers. Fixes
  `Issue #1079 <https://github.com/kiwitcms/Kiwi/issues/1079>`_
- Start Codecov for coverage reports
- Add tests for presense of mysql/psql binaries in container
- Add ``APIPermissionsTestCase`` with example in
  ``TestVersionCreatePermissions``
- Move most test jobs away from Travis CI to GitHub workflows


Translations
~~~~~~~~~~~~

- Updated `Bengali translation <https://crowdin.com/project/kiwitcms/bn#>`_
- Updated `Bulgarian translation <https://crowdin.com/project/kiwitcms/bg#>`_
- Updated `Chinese Simplified translation <https://crowdin.com/project/kiwitcms/zh-CN#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `German translation <https://crowdin.com/project/kiwitcms/de#>`_
- Updated `Hindi translation <https://crowdin.com/project/kiwitcms/hi#>`_
- Updated `Hungarian translation <https://crowdin.com/project/kiwitcms/hu#>`_
- Updated `Indonesian translation <https://crowdin.com/project/kiwitcms/id#>`_
- Updated `Japanese translation <https://crowdin.com/project/kiwitcms/ja#>`_
- Updated `Korean translation <https://crowdin.com/project/kiwitcms/ko#>`_
- Updated `Russian translation <https://crowdin.com/project/kiwitcms/ru#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_
- Updated `Spanish translation <https://crowdin.com/project/kiwitcms/es-ES#>`_
- Updated `Swahili translation <https://crowdin.com/project/kiwitcms/sw#>`_

.. note::

    Some of the translations in Chinese and German and all of the strings in
    Japanese and Korean have been contributed by a non-native speaker and are
    sub-optimal, see
    `OpenCollective #18663 <https://opencollective.com/kiwitcms/expenses/18663>`_.
    If you are a native in these languages and spot strings which don't
    sit well with you we kindly ask you to
    `contribute a better translation <https://kiwitcms.readthedocs.io/en/latest/contribution.html#translation>`_
    via the built-in translation editor!


Kiwi TCMS 8.3 (27 Apr 2020)
---------------------------

**IMPORTANT:** this is a small release which updates 3rd party libraries,
provides several improvements, includes minor API changes and new translations.
It is the first release to include contributions via our
`open source bounty program`_.

Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update django-colorfield from 0.2.2 to 0.3.0
- Update django-simple-history from 2.8.0 to 2.9.0
- Update prismjs from 1.19.0 to 1.20.0
- Update psycopg2 from 2.8.4 to 2.8.5
- Update pygithub from 1.47 to 1.50
- Update python-gitlab from 2.1.2 to 2.2.0
- It is now possible to reopen closed bugs - Fixes
  `Issue #1152 <https://github.com/kiwitcms/Kiwi/issues/1152>`_ (@cmbahadir)
- Visual improvements for Status matrix telemetry:

  - columns now link to test runs
  - tooltips show test run summary

- Show TOTAL in tooltip for Execution trends telemetry
- Self-signed SSL certificate is now built more frequently and is valid
  for 10 years
- Improved documentation around self-signed certificates
- Improved documentation around e-mail backend configuration. Closes
  `Issue #1070 <https://github.com/kiwitcms/Kiwi/issues/1070>`_
  (@Schwarzkrieger)


API
~~~

- Methods ``TestPlan.create``, ``TestPlan.update`` and ``TestRun.update``
  now use Django's ModelForm to properly validate input data against the model
- Method ``TestCase.update`` now also accepts username and email values for
  fields ``author``, ``default_tester`` and ``reviewer``


Refactoring
~~~~~~~~~~~

- Migrate bandit test job to GitHub workflows, Closes
  `Issue #1550 <https://github.com/kiwitcms/Kiwi/issues/1550>`_ (@lcmtwn)
- Migrate doc8 test job to GitHub workflows. Closes
  `Issue #1551 <https://github.com/kiwitcms/Kiwi/issues/1551>`_ (@Prome88)
- Add 2 more tests (Mariyan Garvanski)
- Convert TP edit page to class based view
- Convert forms to ModelForm


Translations
~~~~~~~~~~~~

- Updated `Chinese Simplified translation <https://crowdin.com/project/kiwitcms/zh-CN#>`_
- Updated `German translation <https://crowdin.com/project/kiwitcms/de#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Portuguese, Brazilian translation <https://crowdin.com/project/kiwitcms/pt-BR#>`_
- Updated `Russian translation <https://crowdin.com/project/kiwitcms/ru#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_
- Updated `Vietnamese translation <https://crowdin.com/project/kiwitcms/vi#>`_



Kiwi TCMS 8.2 (03 Apr 2020)
---------------------------

**IMPORTANT:** this is a small release which updates 3rd party libraries,
provides minor improvements, minor API changes and some new translations.


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update bleach from 3.1.1 to 3.1.4
- Update django from 3.0.4 to 3.0.5
- Update django-colorfield from 0.2.1 to 0.2.2
- Update pygithub from 1.46 to 1.47
- Update python-gitlab from 2.0.1 to 2.1.2
- Update marked(js) to version 0.8.2
- Change default MariaDB charset and collation to utf8mb4. Will only affect
  new installations. Closes
  `Issue #327 <https://github.com/kiwitcms/Kiwi/issues/327>`_
- Document ``TCMS_PLAN_ID`` ENV variable supported by automation framework
  plugins
- Test case Search page now allows searching for records containing the
  specified text. Closes #1209 @Schwarzkrieger
- Provide ``../site-packages/tcms_settings_dir/`` when installing Kiwi TCMS
  which is an empty pkgutil-style namespace where other packages can drop
  their configuration
- Hide empty values in Execution trends chart tooltips


API
~~~

- Remove ``Auth.login_krbv()`` method
- Method ``TestRun.update()`` will now accept ``%Y-%m-%d %H:%M:%S``
  timestamp format. The previous format ``%Y-%m-%d`` is also supported
- Method ``TestExecution.create()`` now defaults to first neutral status
  instead of searching for the hard-coded ``IDLE``. That means newly created
  test executions which do not specify status will be created with the first
  neutral status found in the database


Refactoring
~~~~~~~~~~~

- Fix pylint errors. Closes
  `Issue #1510 <https://github.com/kiwitcms/Kiwi/issues/1510>`_ (@cmbahadir)
- Add tests for ``TestRunAdmin.delete_view()`` (Mariyan Garvanski)
- Revert "[l10n] Add Serializer class which returns untranslated models"


Translations
~~~~~~~~~~~~

- Updated `Bulgarian translation <https://crowdin.com/project/kiwitcms/bg#>`_
- Updated `Portuguese, Brazilian translation <https://crowdin.com/project/kiwitcms/pt-BR#>`_



Kiwi TCMS 8.1 (04 Mar 2020)
---------------------------

**IMPORTANT:** this is a small security and improvement release which
also includes several bug fixes, internal refactoring and updated translations.


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Security
~~~~~~~~

- JSON-RPC handler will now HTML escape all strings. This prevents XSS attacks
  via tags, components or anything else which is loaded on the web page via RPC
  and then shown as string. Even if someone saves
  ``<script>alert(123);</script>`` in the database the returned result will be
  HTML escaped and will not be executed as JavaScript!

  .. note::

        This is easy to exploit but people able to do so should have accounts in
        your Kiwi TCMS installation and write privileges on their accounts. If they
        do this means they can cause a lot more damage much more easily!

- Update Django from 3.0.3 to 3.0.4 - fixes security issue CVE-2020-9402:
  Potential SQL injection via ``tolerance`` parameter in GIS functions and
  aggregates on Oracle which we believe does not affect Kiwi TCMS


Improvements
~~~~~~~~~~~~

- Update bleach from 3.1.0 to 3.1.1
- Update django-colorfield from 0.1.15 to 0.2.1
- Update markdown from 3.2 to 3.2.1
- On bug creation send email to assignee. Fixes
  `Issue #1154 <https://github.com/kiwitcms/Kiwi/issues/1154>`_ (Mfon Eti-mfon)
- Make it possible to provide override settings in a directory. Kiwi TCMS will
  respect:

  - ``local_settings.py``
  - ``local_settings_dir/*.py``

  For more information see
  https://kiwitcms.readthedocs.io/en/latest/installing_docker.html#customization
- Allow adding TestPlan to TestCase via UI. Fixes
  `Issue #1021 <https://github.com/kiwitcms/Kiwi/issues/1021>`_
- Add visual representation of failures in TestCase health telemetry
- Add helper text to TestExecutionStatus admin
- Add link to discussion forum in Help menu


API
~~~

- ``TestCase.create()`` method no longer accepts ``product`` or ``product_id``
  fields which have previously been deprecated
- API methods which receive True/False values will no longer parse yes,no,1,0
  values. The only accepted values are boolean constants defined in the calling
  programming language which are then transmitted via XML-RPC or JSON-RPC and
  converted to native boolean on the backend


Bug fixes
~~~~~~~~~

- The number of search results shown per page can now be controlled via
  ``DEFAULT_PAGE_SIZE`` setting, which is 100 by default. Fixes
  `Issue #1210 <https://github.com/kiwitcms/Kiwi/issues/1210>`_ (Ivailo Karabojkov)
- Use comma separated display of components in bug reports. Fixes
  `Issue #1157 <https://github.com/kiwitcms/Kiwi/issues/1157>`_ (Ivailo Karabojkov)
- Update selector for 'Select All' test executions in TestRun page. Fixes
  `Issue #1404 <https://github.com/kiwitcms/Kiwi/issues/1404>`_
- Fix crash when sorting test cases in TestPlan page. Fixes
  `Sentry #KIWI-TCMS-A6 <https://sentry.io/organizations/open-technologies-bulgaria-ltd/issues/1519809326/>`_
- Fix a ``TC-undefined`` displayed in TestCase health telemetry


Refactoring
~~~~~~~~~~~

- Add test for ``TestRunAdmin.change_view()`` (Mariyan Garvanski)
- Remove unused ``showCaseRunsWithSelectedStatus``
- Internal JavaScript updates


Translations
~~~~~~~~~~~~

- Updated `Bulgarian translation <https://crowdin.com/project/kiwitcms/bg#>`_
- Updated `Chinese Simplified translation <https://crowdin.com/project/kiwitcms/zh-CN#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_



Kiwi TCMS 8.0 (12 Feb 2020)
---------------------------

**IMPORTANT:** this is a major release which includes important database and
API changes, several improvements and bug fixes. Multiple API methods are now
incompatible with older releases and extra caution needs to be applied when
upgrading via ``docker-compose.yml`` because newer MariaDB versions are
breaking direct upgrades from existing installations!

Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update Django from 3.0.2 to 3.0.3
- Update django-grappelli from 2.13.3 to 2.14.1
- Update markdown from 3.1.1 to 3.2
- Update python-gitlab from 1.15.0 to 2.0.1
- Update pygithub from 1.45 to 1.46
- Allow customization of test execution statuses via admin.
  For more information see
  https://kiwitcms.readthedocs.io/en/latest/admin.html#test-execution-statuses.
  Fixes `Issue #236 <https://github.com/kiwitcms/Kiwi/issues/236>`_
- Add passing rate chart to Execution trends telemetry
- Documentation updates (@Prome88)


Database
~~~~~~~~

This release adds several migrations which alter the underlying database schema
by renaming multiple columns.

.. warning::

    - SQLite has very poor capabilities for altering schema and it will break
      when run with existing database! If you had deployed Kiwi TCMS with
      SQLite for production purposes you will not be able to upgrade! We recommend
      switching to Postgres first and then upgrading!

    - ``docker-compose.yml`` has been updated from MariaDB 5.5 to MariaDB 10.3.
      The 10.x MariaDB containers change their ``datadir`` configuration from
      ``/var/lib/mysql`` to ``/var/lib/mysql/data``! We recommend first upgrading
      your MariaDB version, using Kiwi TCMS 7.3 and afterwards upgrading to
      Kiwi TCMS 8.0:

      1. Backup existing database with::

            docker exec -it kiwi_db mysqldump -u kiwi -pYourPass kiwi > backup.sql

      2. ``docker-compose down``
      3. ``docker volume rm kiwi_db_data`` - will remove existing data volume
         b/c of incompatibilities between different MariaDB versions
      4. ``docker-compose up`` - will recreate data volume with missing data. e.g.
         ``manage.py showmigrations`` will report that 0 migrations have been applied.
      5. Restore the data from backup::

           cat backup.sql | docker exec -u 0 -i kiwi_db /opt/rh/rh-mariadb103/root/usr/bin/mysql kiwi

         .. note::

            This connects to the database as the root user

      6. Proceed to upgrade your Kiwi TCMS container !


- Remove model fields of type ``AutoField``. They are a legacy construct
  and shouldn't be specified in the source code! Django knows how to add them
  dynamically. These are:

  - ``Tag.id``
  - ``TestCaseStatus.id``
  - ``Category.id``
  - ``PlanType.id``
  - ``TestExecutionStatus.id``

- Remove ``db_column`` attribute from model fields
- Rename several primary key fields to ``id``:

  - ``Build.build_id`` -> ``Build.id``
  - ``TestRun.run_id`` -> ``TestRun.id``
  - ``TestPlan.plan_id`` -> ``TestPlan.id``
  - ``TestCase.case_id`` -> ``TestCase.id``
  - ``TestExecution.case_run_id`` -> ``TestExecution.id``


API
~~~

.. warning::

    The database schema changes mentioned above affect multiple API methods
    in a backwards incompatible way!
    There is possibility that your API scripts will also be affected. You will
    have to adjust those to use the new field names where necessary!

- Methods ``Build.create()``, ``Build.filter()`` and ``Build.update()`` will
  return ``id`` instead of ``build_id`` field
- Method ``TestRun.get_cases()`` will return ``execution_id`` instead of
  ``case_run_id`` field and ``id`` instead of ``case_id`` field
- Methods ``TestRun.add_case()``, ``TestExecution.create()``,
  ``TestExecution.filter()`` and ``TestExecution.update()`` will return
  ``id`` instead of ``case_run_id`` field
- Methods ``TestRun.create()``, ``TestRun.filter()``, ``TestRun.update()`` will
  return ``id`` instead of ``run_id`` field
- Methods ``TestPlan.create()``, ``TestPlan.filter()`` and
  ``TestPlan.update()`` will return ``id`` instead of ``plan_id`` field
- Methods ``TestCase.add_component()``, ``TestCase.create()``,
  ``TestCase.filter()`` and ``TestCase.update()`` will return ``id`` instead
  of ``case_id`` field

.. note::

    Kiwi TCMS automation framework plugins have been updated to work with the
    newest API. At the time of Kiwi TCMS v8.0 release their versions are:

    - kiwitcms-tap-plugin v8.0.1
    - kiwitcms-junit.xml-plugin v8.0.1
    - kiwitcms-junit-plugin v8.0


Bug fixes
~~~~~~~~~

- Allow displaying lists with more then 9 items when reviewing test cases. Fixes
  `Issue #339 <https://github.com/kiwitcms/Kiwi/issues/339>`_ (Mfon Eti-mfon)
- Make ``tcms.tests.storage.RaiseWhenFileNotFound``` capable of finding
  finding static files on Windows which enables development mode for folks
  not using Linux environment. See
  `SO #55297178 <https://stackoverflow.com/questions/55297178>`_ (Mfon Eti-mfon)
- Allow changing test execution status without adding comment. Fixes
  `Issue #1261 <https://github.com/kiwitcms/Kiwi/issues/1261>`_
- Properly refresh test run progress bar when changing statuses. Fixes
  `Issue #1326 <https://github.com/kiwitcms/Kiwi/issues/1326>`_
- Fix a bug where updating test cases from the UI was causing text and various
  other fields to be reset. Fixes
  `Issue #1318 <https://github.com/kiwitcms/Kiwi/issues/1318>`_


Refactoring
~~~~~~~~~~~

- Extract attachments widget to new template. Fixes
  `Issue #1124 <https://github.com/kiwitcms/Kiwi/issues/1124>`_
  (Rosen Sasov)
- Rename RPC related classes. Fixes
  `Issue #682 <https://github.com/kiwitcms/Kiwi/issues/682>`_
  (Rosen Sasov)
- Add new test (Mariyan Garvanski)
- Start using GitHub actions, first for running flake8
- Remove unused ``TestCase.get_previous_and_next()``
- Remove unused ``TestCaseStatus.string_to_instance()``
- Remove unused ``TestCase.create()``
- Remove unused ``json_success_refresh_page()``
- Remove unused fields from ``SearchPlanForm``
- Use JSON-RPC in ``previewPlan()``
- Remove ``toggleTestCaseContents()``, duplicate of
  ``toggleTestExecutionPane()``
- Refactor a few more views to class-based


Translations
~~~~~~~~~~~~

- Updated `Bulgarian translation <https://crowdin.com/project/kiwitcms/bg#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Korean translation <https://crowdin.com/project/kiwitcms/ko#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_
- Updated `Turkish translation <https://crowdin.com/project/kiwitcms/tr#>`_



Kiwi TCMS 7.3 (16 Jan 2020)
---------------------------

**IMPORTANT:** this is a critical security update for
**CVE-2019-19844: Potential account hijack via password reset form!**

Also migrates to Django 3.0 and includes several other improvement
and bug-fixes!


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update Django from 2.2.8 to 3.0.2
- Update python-gitlab from 1.13.0 to 1.15.0
- Update pygithub from 1.44.1 to 1.45
- Update django-grappelli from 2.13.2 to 2.13.3
- Bump django-uuslug from 1.1.9 to 1.2.0
- Bump django-attachments from 1.4.1 to 1.5
- Bump django-vinaigrette from 1.2.0 to 2.0.1
- Update marked to version 0.8.0
- Update prismjs to version 1.19.0
- Generalize existing ``kiwitcms.telemetry.plugins`` handling code by
  renaming the entry point to ``kiwitcms.plugins``
- Refactor views to class based (Svetlozar Stoyanov)
- Teach Kiwi TCMS to automatically report bugs to GitHub when the user
  selects such action. Fall back to opening a new browser window for
  manually entering the bug if something goes wrong


Database
~~~~~~~~

- When migrating from the older ``Bug`` model to ``LinkReference`` skip
  bugs which are attached directly to test cases instead of test executions.
  See `SO #59321756 <https://stackoverflow.com/questions/59321756/>`_
- Remove ``AutoField.max_length`` because it is ignored by Django 3


API
~~~

- ``TestCase.update()`` method now allows to update the ``author`` field. Fixes
  `Issue #630 <https://github.com/kiwitcms/Kiwi/issues/630>`_


Bug fixes
~~~~~~~~~

- Modify template pass ``object`` as ``test_plan``. Fixes
  `Issue #1307 <https://github.com/kiwitcms/Kiwi/issues/1307>`_ (Ed Oswald S. Go)
- Enable version selection in test plan search page. Fixes
  `Issue #1276 <https://github.com/kiwitcms/Kiwi/issues/1276>`_
- Apply percentage rounding for completed test executions. Fixes
  `Issue #1230 <https://github.com/kiwitcms/Kiwi/issues/1230>`_
- Fix a logical bug in conditional expression when deciding whether or not
  reporting bugs to selected issue tracker is disabled


Refactoring
~~~~~~~~~~~

- Add code of conduct. Fixes
  `Issue #1185 <https://github.com/kiwitcms/Kiwi/issues/1185>`_ (Rosen Sasov)
- Add test for ``KIWI_DONT_ENFORSE_HTTPS``. Closes
  `Issue #1274 <https://github.com/kiwitcms/Kiwi/issues/1274>`_
- Replace ``ugettext_lazy`` with ``gettext_lazy`` for Django 3
- Remove ``BaseCaseSearchForm.bug_id`` field
- Refactor testcase edit view to class-based
- Happy New Year pylint


Translations
~~~~~~~~~~~~

- Updated `Chinese Simplified translation <https://crowdin.com/project/kiwitcms/zh-CN#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_
- Updated `Vietnamese translation <https://crowdin.com/project/kiwitcms/vi#>`_



Kiwi TCMS 7.2 (08 Dec 2019)
---------------------------


**IMPORTANT:** this is an improvement & bug fix release which includes
new database migrations and API methods, internal refactoring and updated
translations.


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Base docker image to new CentOS 8
- Update Django from 2.2.6 to 2.2.8
- Update django-contrib-comments from 1.9.1 to 1.9.2
- Update django-grappelli from 2.13.1 to 2.13.2
- Update django-modern-rpc from 0.11.1 to 0.12.0
- Update django-simple-history from 2.7.3 to 2.8.0
- Update mysqlclient from 1.4.4 to 1.4.6
- Update pygithub from 1.44 to 1.44.1
- Update python-gitlab from 1.12.1 to 1.13.0
- Several documentation updates


Database migrations
~~~~~~~~~~~~~~~~~~~

- Add new database fields ``weight``, ``icon`` and ``color`` to
  ``TestExecutionStatus`` and adjust existing code to work with them.
  This is a necessary step before allowing customization of test execution
  statuses, see
  `Issue #236 <https://github.com/kiwitcms/Kiwi/issues/236>`_


API
~~~

- RPC method ``TestExecution.add_comment()`` now requires
  ``django_comments.add_comment`` permission
- Add new RPC method ``TestExecution.remove_comment()``
- Add new RPC method ``TestCase.add_comment()``
- Add new RPC method ``TestCase.remove_comment()``


Bug fixes
~~~~~~~~~

- ``testplans.views.DeleteCasesView`` now requires
  ``testplans.change_testplan`` permission (Svetlomir Balevski)
- ``testplans.views.ReorderCasesView`` now requires
  ``testplans.change_testplan`` permission (Svetlomir Balevski)
- Fix counting bug in execution trends telemetry
- Fix several telemetry queries to still show data in the corner case
  where test cases have been deleted from a TestPlan but test runs
  are still available
- Fix broken bulk menu in TestRun page when (translated) status names
  are too long
- Automatically expand TestExecution comment history if there are comments
  present. Fixes
  `Issue #349 <https://github.com/kiwitcms/Kiwi/issues/349>`_ (Matt Porter)
- Document timezone settings and show current server time in navbar. Fixes
  `Issue #1206 <https://github.com/kiwitcms/Kiwi/issues/1206>`_
- Check for permissions in HTML template. Closes
  `Issue #961 <https://github.com/kiwitcms/Kiwi/issues/961>`_
- Document bug tracker integration support. Fixes
  `Issue #698 <https://github.com/kiwitcms/Kiwi/issues/698>`_
- Delete comments when TestCase and TestExecution are removed. Closes
  `Issue #1028 <https://github.com/kiwitcms/Kiwi/issues/1028>`_


Refactoring
~~~~~~~~~~~

- Pylint fixes (Mariyan Garvanski)
- Use ``django.utils.timezone.now()`` instead of ``datetime.now()``. Closes
  `Issue #545 <https://github.com/kiwitcms/Kiwi/issues/545>`_
- Use JSON-RPC instead of backend views when working with comments. Resolves
  `Issue #960 <https://github.com/kiwitcms/Kiwi/issues/960>`_
- Remove ``tcms.core.contrib.comments`` module. Closes
  `Issue #959 <https://github.com/kiwitcms/Kiwi/issues/959>`_
- Remove ``label=`` attribute from form field. Fixes
  `Issue #652 <https://github.com/kiwitcms/Kiwi/issues/652>`_
- Move and rename XML-RPC forms. Resolves
  `Issue #681 <https://github.com/kiwitcms/Kiwi/issues/681>`_
- Convert ``testplans.views.DeleteCasesView`` to JSON-RPC
- Refactor more views from function based to class based
- Remove duplicate JavaScript


Translations
~~~~~~~~~~~~

- Updated `Bulgarian translation <https://crowdin.com/project/kiwitcms/bg#>`_
- Updated `Chinese Traditional translation <https://crowdin.com/project/kiwitcms/zh-TW#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_



Kiwi TCMS 7.1 (29 Oct 2019)
---------------------------

**IMPORTANT:** this is a small improvement update which includes
database schema and API changes, several other improvements,
internal refactoring and updated translations.


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update django from 2.2.5 to 2.2.6
- Update python-gitlab from 1.11.0 to 1.12.1
- Update pygithub from 1.43.8 to 1.44
- Update psycopg2 from 2.8.3 to 2.8.4
- Add help tooltips in all telemetry pages
- Better styling for checkboxes in 'Add hyperlink' dialog,
  part of TestRun page
- Add hyperlink validation. Fixes
  `Issue #1147 <https://github.com/kiwitcms/Kiwi/issues/1147>`_

Database migrations
~~~~~~~~~~~~~~~~~~~

- Add ``bugs`` permissions to ``Tester`` group. Will make any difference
  only if upgrading from existing installation


API
~~~

- New method ``Bug.remove()``


Bug fixes
~~~~~~~~~

- Always build with the latest versions of translations
- Add 'Delete' menu item in Bugs page. Fixes
  `Issue #1153 <https://github.com/kiwitcms/Kiwi/issues/1153>`_
- When deleting hyperlink from TestExecution hide the actual UI
  elements from the page
- Fix failure to delete TCs when the number of TCs inside TP is greater
  than 100. Fixes
  `Issue #1149 <https://github.com/kiwitcms/Kiwi/issues/1149>`_ and
  `Sentry KIWI-TCMS-8F <https://sentry.io/organizations/open-technologies-bulgaria-ltd/issues/1245504316/>`_


Refactoring
~~~~~~~~~~~

- Rename directory ``xmlrpc`` to ``rpc`` and pylint updates. Refs
  `Issue #682 <https://github.com/kiwitcms/Kiwi/issues/682>`_
  (Matej Aleksandrov, Sinergise)
- Remove labels from form fields, Refs
  `Issue #652 <https://github.com/kiwitcms/Kiwi/issues/652>`_ (Azmi YÜKSEL)
- New base class for tests around permissions (Svetlomir Balevski)
- New "blueprint" test case around permissions to make testing in this area
  more robust
- Refactor many views from function based to class based
- Update stale tests in ``tcms/core/tests/`` and make sure they aren't ignored
  by the test runner
- Remove empty class ``XMLRPCBaseCaseForm``
- Remove ``XMLRPCNewCaseForm``, duplicate of ``NewCaseForm``
- Remove ``rpc.forms.UpdateCaseForm`` in favor of ``XMLRPCUpdateCaseForm``
- Update only English sources with new strings as a temporary workaround b/c
  Crowdin uses different formatting heuristics than gettext. This will minimize
  the number of .po format changes
- A few pylint fixes


Translations
~~~~~~~~~~~~

- Updated `Albanian translation <https://crowdin.com/project/kiwitcms/sq#>`_ - 97%
- Updated `Bulgarian translation <https://crowdin.com/project/kiwitcms/bg#>`_ - 91%
- Updated `Chinese Simplified <https://crowdin.com/project/kiwitcms/zh-CN#>`_ - 71%
- Updated `Greek translation <https://crowdin.com/project/kiwitcms/el#>`_ - 44%
- Updated `Italian translation <https://crowdin.com/project/kiwitcms/it#>`_ - 97%
- Updated `Japanese translation <https://crowdin.com/project/kiwitcms/ja#>`_ - 0%
- Updated `Macedonian translation <https://crowdin.com/project/kiwitcms/mk#>`_ - 11%
- Updated `Russian translation <https://crowdin.com/project/kiwitcms/ru#>`_ - 97%
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_ - 100%
- Updated `Spanish translation <https://crowdin.com/project/kiwitcms/es-ES#>`_ - 96%
- Updated `Turkish translation <https://crowdin.com/project/kiwitcms/tr#>`_ - 97%



Kiwi TCMS 7.0 (24 Sep 2019)
---------------------------

**IMPORTANT:** this is a major release which includes security updates,
significant database schema and API changes, many improvements,
removed functionality, bug fixes, substantial internal refactoring and
several new languages.


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Security
~~~~~~~~

- API method ``BugSystem.filter()`` has been removed (now unused) but
  it was possible to use this method to steal passwords or keys used for
  Issue Tracker integration. This vulnerability could be exploited by
  users logged into Kiwi TCMS and is classified as medium severity!
  We advise you to change your integration API keys and passwords
  immediately!


Improvements
~~~~~~~~~~~~

- Update Django from 2.2.4 to 2.2.5
- Update django-uuslug from 1.1.8 to 1.1.9
- Update mysqlclient from 1.4.2.post1 to 1.4.4
- Update python-bugzilla from 2.2.0 to 2.3.0
- Update python-gitlab from 1.10.0 to 1.11.0
- Update patternfly from 3.59.3 to 3.59.4
- Reduce docker image size from 1.01 GB to 577 MB
- Add TestCase Health telemetry
- Add support for Redmine issue tracker. Fixes
  `Issue #41 <https://github.com/kiwitcms/Kiwi/issues/41>`_ (Jesse C. Lin)
- Add breathing room around HTML form's submit buttons (Rady Madjev)
- New TestRun page action: bulk-add hyperlinks to TestExecution(s)
- Make it possible to disable HTTPS by specifying the
  ``KIWI_DONT_ENFORCE_HTTPS`` environment variable! Fixes
  `Issue #1036 <https://github.com/kiwitcms/Kiwi/issues/1036>`_ (Marco Descher)
- Documentation updates, including internal style checker. Fixes
  `Issue #1000 <https://github.com/kiwitcms/Kiwi/issues/1000>`_ (Prome88)
- When linking a TestExecution to a defect and choosing to update the
  Issue Tracker Kiwi TCMS will not add a comment pointing back to
  TR ID/summary/URL and TE ID/summary. This provides more detailed information
  about the reproducer instead of just linking to a TestCase without any
  specific execution details like we did in the past
- Display additional defect information via Issue Tracker integration.
  On Patternfly pages which show defect URLs this is accessible via a
  small info icon. Fixes
  `Issue #117 <https://github.com/kiwitcms/Kiwi/issues/117>`_
- Add minimalistic defect tracker functionality. Fixes
  `Issue #699 <https://github.com/kiwitcms/Kiwi/issues/699>`_

  - integrated with Issue Tracker integration layer as if it was
    an external system
  - when adding hyperlink to TestExecition (also via API method
    ``TestExecution.add_link()``) this is special cased and the
    references between ``Bug`` and ``TestExecution`` are always updated
  - when clicking 'Report bug' from inside Test Execution the new
    defect is reported automatically and a new browser window opens to
    display the information


Database migrations
~~~~~~~~~~~~~~~~~~~

- Tell the migration planner to apply
  ``testruns.0006_rename_test_case_run_to_test_execution`` after
  ``linkreference.0001_squashed``. This enables subsequent migrations
  and new functionality to be applied without crashing.

    .. warning::

        Django should be able to handle this automatically both for
        existing installations and for new ones. In any case make sure
        you backup your data first and make a dry-run to verify that
        nothing breaks!

- Remove fields ``url_reg_exp``, ``validate_reg_exp`` and ``description`` from
  ``BugSystem`` model
- Update the following fields in ``LinkReference`` model:

  - rename ``test_case_run`` to ``execution``
  - add indexing for ``created_on`` and ``url``
  - add ``is_defect`` field

- Apply ``LinkReference`` permissions to default group ``Tester``. Fixes
  `Issue #881 <https://github.com/kiwitcms/Kiwi/issues/881>`_

    .. warning::

        Administrators of existing applications will need to
        apply these permissions by hand via the Admin section.

- Remove ``testcases.Bug`` model, replaced with ``LinkReference``.
  Closes `Issue #1029 <https://github.com/kiwitcms/Kiwi/issues/1029>`_ and
  obsoletes `Issue #320 <https://github.com/kiwitcms/Kiwi/issues/320>`_.

    .. note::

        Linking bugs to TestExecution is now performed via URLs instead of
        keeping a reference to BUG-ID and trying to reconstruct the URL
        on the fly.

    .. warning::

        The model named ``Bug`` which is added by subsequent migrations
        refers to defects reported into Kiwi TCMS minimalistic defect tracker!

- New model ``bugs.Bug`` is now available. Permissions of type
  ``bugs | bug | Can ...`` will be applied to the default group named
  ``Tester`` only for new installations.

    .. warning::

        Administrators of existing applications will need to
        apply these permissions by hand via the Admin section.


API
~~~

- ``TestExecution.add_link()`` method now returns serialized
  ``LinkReference`` object.
- ``TestExecution.remove_link()`` method now accepts one parameter of type
  ``dict`` used to filter the objects which to remove
- ``TestExecution.get_links()`` method now accepts one parameter of type
  ``dict`` instead of ``int``
- ``TestExecution.add_link()`` method signature changed from
  (int, str, str) to (dict), where the single parameter holds field values for
  the ``LinkReference`` model
- Remove ``TestExecution.add_bug()`` method, use ``TestExecution.add_link()``
- Remove ``TestExecution.remove_bug()`` method, use
  ``TestExecution.remove_link()``
- Remove ``TestCase.add_bug()`` method
- Remove ``TestCase.remove_bug()`` method
- Remove ``Bug.remove()`` method, use ``TestExecution.remove_link()``
- Remove ``Bug.create()`` method, use ``TestExecution.add_link()``
- Add method ``Bug.details()`` which together with the underlying
  ``IssueTracker.details()`` is the foundation of how Kiwi TCMS fetches
  extra details from the issue tracking system. The default implementation
  uses OpenGraph protocol to collect the data that will be shown. You may
  override ``.details()`` for each issue tracker (or add your own IT) to
  extend this functionality. Information is cached for 1 hour by default.
  References
  `Issue #117 <https://github.com/kiwitcms/Kiwi/issues/117>`_
- Add methods ``Bug.add_tag()`` and ``Bug.remove_tag()``
- Existing method with name ``Bug.filter()`` has changed behavior. It is
  now used to query objects from Kiwi TCMS minimalistic defect tracker


Removed functionality
~~~~~~~~~~~~~~~~~~~~~

- Remove ``IssueTrackerType.all_issues_link()`` method. This was used in
  TestRun Report page to show a single link that will open all bugs in the
  Issue Tracker. Most trackers don't support this and the UI portion has
  been rewritten
- Remove ``LinkOnly`` issue tracker - obsolete because all defects are
  now added to TestExecutions via their URLs
- Remove bulk-add/bulk-remove of bugs in TestRun page, replaced by bulk-add
  for hyperlinks


Settings
~~~~~~~~

- Respect the ``CACHES`` setting, see
  `Django docs <https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-CACHES>`_
  for more info. Initially this setting is used to cache defect details
  received via Issue Tracker integration. See
  `Issue #117 <https://github.com/kiwitcms/Kiwi/issues/117>`_


Bug fixes
~~~~~~~~~

- Don't auto-download FontAwesome for SimpleMDE. Resolves icons disappearing
  on pages which have the markdown editor. Fixes
  `Issue #905 <https://github.com/kiwitcms/Kiwi/issues/905>`_
- Reorder HTML elements so Delete button is still visible in TestCase review
  comment section. Fixes
  `Issue #1013 <https://github.com/kiwitcms/Kiwi/issues/1013>`_ (Rady Madjev)
- Remove section that displays bugs in TestExecution container. Bugs are now
  denoted by a small icon next to their hyperlink. Closes
  `Issue #475 <https://github.com/kiwitcms/Kiwi/issues/475>`_
- Cache Issue Tracker connections per ``base_url``. Fixes
  `Issue #290 <https://github.com/kiwitcms/Kiwi/issues/290>`_



Refactoring
~~~~~~~~~~~

- Lots of refactoring from function based views to class based views
  (Rady Madjev)
- Use JavaScript and the API to remove case execution instead of
  dedicated backend function (Rady Madjev)
- Update pylint directives around missing permissions (Svetlomir Balevski)
- Fix typo in identifier. Fixes
  `CID 344186 <https://scan4.coverity.com/reports.htm#v38579/p14953/fileInstanceId=65904319&defectInstanceId=11526612&mergedDefectId=344186&eventId=1>`_
- Use ``TestExecution.add_link()`` and ``TestExecution.remove_link()`` in UI
  instead of dedicated backend function.
- Remove unused LinkReference views, forms and tests modules


Translations
~~~~~~~~~~~~

- Introduce a translation mode where you can translate the interface via
  in-context editor. For more information see
  `Translation guide <https://kiwitcms.readthedocs.io/en/latest/contribution.html#translation>`_.
  Fixes `Issue #1098 <https://github.com/kiwitcms/Kiwi/issues/1098>`_
- Updated `Albanian translation <https://crowdin.com/project/kiwitcms/sq#>`_
- Updated `Bulgarian translation <https://crowdin.com/project/kiwitcms/bg#>`_
- Updated `Chinese Traditional translation <https://crowdin.com/project/kiwitcms/zh-TW#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Greek translation <https://crowdin.com/project/kiwitcms/el#>`_
- Updated `Italian translation <https://crowdin.com/project/kiwitcms/it#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_
- Updated `Turkish translation <https://crowdin.com/project/kiwitcms/tr#>`_

For more information check-out
`all supported languages <https://crowdin.com/project/kiwitcms>`_.
To request new language
`click here <https://github.com/kiwitcms/Kiwi/issues/new?title=Request+new+language:+...&body=Please+enable+...+language+in+Crowdin>`_!



Kiwi TCMS 6.11 (02 Aug 2019)
----------------------------


**IMPORTANT:** this is a security and improvement update which updates
many internal dependencies, adds 2 new Telemetry reports, updates
TestPlan and TestCase cloning pages and provides several other
improvements and bug fixes. Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Security
~~~~~~~~

- Update Django from 2.2.2 to 2.2.4, see
  `2.2.4 release notes <https://docs.djangoproject.com/en/2.2/releases/2.2.4/>`_
- Update marked to version 0.7.0, see
  `0.7.0 release notes <https://github.com/markedjs/marked/releases/tag/v0.7.0>`_


Improvements
~~~~~~~~~~~~

- Update python-gitlab from 1.8.0 to 1.10.0
- Update django-grappelli from 2.12.3 to 2.13.1
- Update django-simple-history from 2.7.2 to 2.7.3
- Update django-attachments to 1.4.1
- Update PyGithub from 1.43.7 to 1.43.8
- Update patternfly to version 3.59.3
- Update prismjs to version 1.17.0
- Add Testing Status Matrix telemetry
- Add Testing Execution Trends telemetry
- Make it possible to attach files directly inside Test Plan page
- Make it possible to attach files directly inside Test Execution widget
- Convert Clone TestPlan page to Patternfly, greatly simplify the UI
  and update behavior:

  - Cloned TP author will always be set to the current user
  - Cloned TC author will always be set to the current user
  - Always keep the original default tester for test cases when cloning
  - Refactor to class based view
  - Fix a problem where Version values failed form validation b/c
    we've been trying to filter based on non-existing field
    ``product_id`` instead of just ``product``
  - Fixes a problem where erroneous Version value was shown in the UI

- Convert Clone TestCase page to Patternfly, greatly simplify the UI
  and update behavior. Fixes
  `Issue #838 <https://github.com/kiwitcms/Kiwi/issues/838/>`_:

  - Allow cloning into multiple test plans
  - Remove 'Filter another plan' option. Will be replaced by
    'Add TP to TC', see
    `Issue #1021 <https://github.com/kiwitcms/Kiwi/issues/1021>`_
  - Always update sortkey. Cloned TC will show at the bottom of the
    TestPlan
  - Cloned TC author will always be set to the current user
  - Always keep the original default tester


API
~~~

- First parameter of RPC method ``Bug.report()``
  has been renamed from ``test_case_run_id`` to ``execution_id``. This may
  break existing API scripts which try to pass this argument by name
  instead of by position!


Settings
~~~~~~~~

- Allow ENV variables ``KIWI_USE_TZ`` and ``KIWI_TIME_ZONE`` to control
  settings ``USE_TZ`` and ``TIME_ZONE``. Fixes
  `Issue #982 <https://github.com/kiwitcms/Kiwi/issues/982/>`_ (Jason Yi)


Bug fixes
~~~~~~~~~

- Fix wrong permission label when deleting comments. Fixes
  `Issue #1010 <https://github.com/kiwitcms/Kiwi/issues/1010/>`_


Refactoring
~~~~~~~~~~~

- Disable unnecessary pylint messages for missing-permission-required
  checker (Svetlomir Balevski)
- Remove unnecessary ``from_plan`` URL variable making cleaner URLs
- kiwi_lint: Don't check nested functions for permissions
- Remove and regroup JavaScript functions
- Instruct pyup-bot to monitor ``requirements/tarballs.txt`` for updates


Translations
~~~~~~~~~~~~

- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_



Kiwi TCMS 6.10 (18 June 2019)
-----------------------------


**IMPORTANT:** this is a small security and improvement update.
Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Security
~~~~~~~~

- Update Django from 2.2.1 to 2.2.2 for medium severity
  CVE-2019-12308 (XSS), CVE-2019-11358 (jQuery).
  `More info <https://docs.djangoproject.com/en/2.2/releases/2.2.2/>`_
- Add missing permission checks for menus in Test run page UI template.
  Permission check added for TestExecution status and comment menu.
  References `Issue #716 <https://github.com/kiwitcms/Kiwi/issues/716>`_
- Re-enable static analysis with ``bandit`` and ``Coverity Scan`` in
  Travis CI (Svetlomir Balevski)


Improvements
~~~~~~~~~~~~

- Update psycopg2 from 2.8.2 to 2.8.3
- Update markdown from 3.1 to 3.1.1
- Update patternfly to version 3.59.2
- Override ``PasswordResetForm`` because ``Site.objects.get_current()``
  didn't produce correct results when working with ``kiwitcms-tenants``
- Show column ``is_active`` in user admin page


Refactoring
~~~~~~~~~~~

- Add test for ``email_case_deletion()`` (Rik)
- New linter to warn about usage of ``AutoField``. Fixes
  `Issue #737 <https://github.com/kiwitcms/Kiwi/issues/737>`_ (Ivo Donchev, HackSoft)
- New linter to discover empty classed. Fixes
  `Issue #739 <https://github.com/kiwitcms/Kiwi/issues/739>`_ (Daniel Goshev)
- New linter to warn about usage of ``OneToOneField``. Fixes
  `Issue #735 <https://github.com/kiwitcms/Kiwi/issues/735>`_ (George Goranov)
- New linter to warn about usage of function based views. Fixes
  `Issue #734 <https://github.com/kiwitcms/Kiwi/issues/734>`_ (Yavor Lulchev, Uber)
- New linter to discover Python files in directories without ``__init__.py``. Fixes
  `Issue #790 <https://github.com/kiwitcms/Kiwi/issues/790>`_



Kiwi TCMS 6.9 (15 May 2019)
---------------------------

**IMPORTANT:** this is a small improvement and bug-fix update which introduces
our first telemetry report: testing breakdown. Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update mysqlclient from 1.4.2 to 1.4.2.post1
- Ship with prism.js so it can be used for syntax highlighting
- Add Testing Breakdown telemetry
- Mark more strings for translations
- Add ``delete_user()`` function which can delete data across
  Postgre schemas (if kiwitcms-tenants add-on is installed)


API
~~~

- Remove deprecated ``TestCaseRun.`` API methods. Use the new
  ``TestExecution.`` methods introduced in v6.7. Fixes
  `Issue #889 <https://github.com/kiwitcms/Kiwi/issues/889/>`_


Bug fixes
~~~~~~~~~

- Fix typos in documentation (@Prome88)
- Fix ``TemplateParseError`` in email templates when removing test cases.
  On-delete email notification is now sent properly


Refactoring
~~~~~~~~~~~

- Add more tests around TestRun/TestExecution menu permissions
- Minor pylint fixes


Translations
~~~~~~~~~~~~

- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_


Kiwi TCMS 6.8 (03 May 2019)
---------------------------

**IMPORTANT:** this is a small improvement and bug-fix update.
Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update Django from 2.2 to 2.2.1
- Update django-simple-history from 2.7.0 to 2.7.2
- Update django-grappelli from 2.12.2 to 2.12.3
- Update psycopg2 from 2.8 to 2.8.2
- Update pygithub from 1.43.6 to 1.43.7
- Upgrade pip and setuptools inside Docker image
- Update documentation with newer screenshots and updated Tutotial. Fixes
  `Issue #837 <https://github.com/kiwitcms/Kiwi/issues/837/>`_ (@Prome88)
- Document how to enable public read-only views
- Remove deprecated documentation section about Bugzilla authentication
- Install PostgreSQL libraries in Docker image which makes it easier to
  switch the DB backend without rebuilding the entire image
- Remove npm, libxml2-devel and libxslt-devel from Docker image
- Database engine configuration now respects the ``KIWI_DB_ENGINE`` environment
  variable which defaults to ``django.db.backends.mysql``. This will make it
  easier for admins to change DB engine by updating their
  ``docker-compose.yml``


Bug fixes
~~~~~~~~~

- Pin bootstrap-switch to version 3.3.4 in ``package.json``. Fixes
  `Issue #916 <https://github.com/kiwitcms/Kiwi/issues/916/>`_


Translations
~~~~~~~~~~~~

- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_
- Updated `Russian translation <https://crowdin.com/project/kiwitcms/ru#>`_
- New language `Czech <https://crowdin.com/project/kiwitcms/cz#>`_


Refactoring
~~~~~~~~~~~

- Don't use ``Site.objects.get_current()`` because it has an internal cache
  and causes email notifications from tenants to use the wrong URL
- More changes around renaming of TestCaseRun to TestExecution



Kiwi TCMS 6.7 (06 April 2019)
-----------------------------

**IMPORTANT:** this is a small improvement and bug-fix update.
Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update Django from 2.1.7 to 2.2
- Update markdown from 3.0.1 to 3.1
- Update psycopg2 from 2.7.7 to 2.8
- Update pygithub from 1.43.5 to 1.43.6
- Update bleach-whitelist from 0.0.9 to 0.0.10
- Update marked(.js) to version 0.6.2
- Support arbitrary depth for ``MENU_ITEMS`` setting
- Support auto-discovery of 3rd party Telemetry plugins, see
  `documentation <https://kiwitcms.readthedocs.io/en/latest/telemetry/index.html>`_


Database migrations
~~~~~~~~~~~~~~~~~~~

- Rename ``TestCaseRun`` to ``TestExecution`` including renaming existing
  permissions
- Rename ``TestCaseRunStatus`` to ``TestExecutionStatus``


API
~~~

- Rename ``TestCaseRun.*`` to ``TestExecution.*``
- Rename ``TestCaseRunStatus.*`` to ``TestExecution.*``
- This version keeps the old names for backwards compatibility reasons


Bug fixes
~~~~~~~~~

- Prompt user before deleting attachments. Fixes
  `Issue #867 <https://github.com/kiwitcms/Kiwi/issues/867>`_ (Martin Jordanov)
- ``email_case_deletion()`` format error fixed so notifications when
  test cases are deleted are not sent (Rik)


Refactoring
~~~~~~~~~~~

- Remove unused images
- Install ``node_modules/`` under ``tcms/`` and include it inside PyPI tarball


Translations
~~~~~~~~~~~~

- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_



Kiwi TCMS 6.6 (19 Mar 2019)
---------------------------

**IMPORTANT:** this is a medium severity security update, improvement and
bug-fix update. Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Security
~~~~~~~~

- Explicitly require marked v0.6.1 to fix medium severity ReDoS vulnerability.
  See `SNYK-JS-MARKED-73637 <https://snyk.io/vuln/SNYK-JS-MARKED-73637>`_


Improvements
~~~~~~~~~~~~

- Update ``python-gitlab`` from 1.7.0 to 1.8.0
- Update ``django-contrib-comments`` from 1.9.0 to 1.9.1
- More strings marked as translatable (Christophe CHAUVET)
- When creating new TestCase you can now change notification settings.
  Previously this was only possible during editing
- Document import-export approaches. Closes
  `Issue #795 <https://github.com/kiwitcms/Kiwi/issues/795>`_
- Document available test automation plugins
- Improve documentation around Docker customization and SSL termination
- Add documentation example of reverse rroxy configuration for HAProxy
  (Nicolas Auvray)
- ``TestPlan.add_case()`` will now set the sortkey to highest in plan + 10
  (Rik)
- Add ``LinkOnly`` issue tracker. Fixes
  `Issue #289 <https://github.com/kiwitcms/Kiwi/issues/289>`_
- Use the same HTML template for both TestCase new & edit
- New API methods for adding, removing and listing attachments. Fixes
  `Issue #446 <https://github.com/kiwitcms/Kiwi/issues/446>`_:

  - TestPlan.add_attachment()
  - TestCase.add_attachment()
  - TestPlan.list_attachments()
  - TestCase.list_attachments()
  - Attachments.remove_attachment()


Database migrations
~~~~~~~~~~~~~~~~~~~

- Populate missing ``TestCase.text`` history.
  In version 6.5 the ``TestCase`` model was updated to store the text
  into a single field called ``text`` instead of 4 separate fields.
  During that migration historical records were updated to have
  the new ``text`` field but values were not properly assigned.

  The "effect" of this is that in TestCaseRun records you were not
  able to see the actual text b/c it was None.

  This change ammends ``0006_merge_text_field_into_testcase_model`` for
  installations which have not yet migrated to 6.5 or later. We also
  provide the data-only migration ``0009_populate_missing_text_history``
  which will inspect the current state of the DB and copy the text to
  the last historical record.


Removed functionality
~~~~~~~~~~~~~~~~~~~~~

- Remove legacy reports. Closes
  `Issue #657 <https://github.com/kiwitcms/Kiwi/issues/657>`_
- Remove "Save & Continue" functionality from TestCase edit page
- Renamed API methods:

  - ``TestCaseRun.add_log()``    -> ``TestCaseRun.add_link()``
  - ``TestCaseRun.remove_log()`` -> ``TestCaseRun.remove_link()``
  - ``TestCaseRun.get_logs()``   -> ``TestCaseRun.get_links()``

  These methods work with URL links, which can be added or removed to
  test case runs.


Bug fixes
~~~~~~~~~

- Remove hard-coded timestamp in TestCase page template, References
  `Issue #765 <https://github.com/kiwitcms/Kiwi/issues/765>`_
- Fix handling of ``?from_plan`` URL parameter in TestCase page
- Make ``TestCase.text`` occupy 100% width when rendered. Fixes
  `Issue #798 <https://github.com/kiwitcms/Kiwi/issues/798>`_
- Enable ``markdown.extensions.tables``. Fixes
  `Issue #816 <https://github.com/kiwitcms/Kiwi/issues/816>`_
- Handle form erros and default values for TestPlan new/edit. Fixes
  `Issue #864 <https://github.com/kiwitcms/Kiwi/issues/864>`_
- Tests + fix for failing TestCase rendering in French
- Show color-coded statuses on dashboard page when seen with non-English
  language
- Refactor check for confirmed test cases when editting to work with
  translations
- Fix form values when filtering test cases inside TestPlan. Fixes
  `Issue #674 <https://github.com/kiwitcms/Kiwi/issues/674>`_ (@marion2016)
- Show delete icon for attachments. Fixes
  `Issue #847 <https://github.com/kiwitcms/Kiwi/issues/847>`_


Refactoring
~~~~~~~~~~~

- Remove unused ``.current_user`` instance attribute
- Remove ``EditCaseForm`` and use ``NewCaseForm`` instead, References
  `Issue #708 <https://github.com/kiwitcms/Kiwi/issues/708>`_,
  `Issue #812 <https://github.com/kiwitcms/Kiwi/issues/812>`_
- Fix "Select All" checkbox. Fixes
  `Issue #828 <https://github.com/kiwitcms/Kiwi/issues/828>`_ (Rady)


Translations
~~~~~~~~~~~~

- Updated `Chinese Simplified translation <https://crowdin.com/project/kiwitcms/zh-CN#>`_
- Updated `Chinese Traditional translation <https://crowdin.com/project/kiwitcms/zh-TW#>`_
- Updated `German translation <https://crowdin.com/project/kiwitcms/de#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_
- Changed misspelled source string
  ``Requirments`` -> ``Requirements`` (@Prome88)



tcms-api 5.3 (24 Feb 2019)
--------------------------

- Add ``plugin_helpers.Backend.add_comment()`` which allows plugins to add
  comments to test executions, for example a traceback


Kiwi TCMS 6.5.3 (11 Feb 2019)
-----------------------------

**IMPORTANT:** this is a security, improvement and bug-fix update that includes
new versions of Django, includes several database migrations and fixes
several bugs.


Security
~~~~~~~~

- Update Django from 2.1.5 to 2.1.7. Fixes CVE-2019-6975:
  Memory exhaustion in ``django.utils.numberformat.format()``


Improvements
~~~~~~~~~~~~

- Update mysqlclient from 1.4.1 to 1.4.2
- Multiple template strings marked as translatable (Christophe CHAUVET)


Database migrations
~~~~~~~~~~~~~~~~~~~

- Email notifications for TestPlan and TestCase now default to True
- Remove ``TestPlanEmailSettings.is_active`` field


API
~~~

- New method ``Bug.report()``, References
  `Issue #18 <https://github.com/kiwitcms/Kiwi/issues/18>`_
- Method ``Bug.create()`` now accepts parameter ``auto_report=False``


Translations
~~~~~~~~~~~~

- Updated `German translation <https://crowdin.com/project/kiwitcms/de#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_


Bug fixes
~~~~~~~~~

- Show the user who actually tested a TestCase instead of hard-coded value. Fixes
  `Issue #765 <https://github.com/kiwitcms/Kiwi/issues/765>`_
- Properly handle pagination button states and page numbers. Fixes
  `Issue #767 <https://github.com/kiwitcms/Kiwi/issues/767>`_
- Add TestCase to TestPlan if creating from inside a TestPlan. Fixes
  `Issue #777 <https://github.com/kiwitcms/Kiwi/issues/777>`_
- Made TestCase text more readable. Fixes
  `Issue #764 <https://github.com/kiwitcms/Kiwi/issues/764>`_
- Include missing templates and static files from PyPI tarball


Refactoring
~~~~~~~~~~~

- Use ``find_packages()`` when building PyPI tarball
- Install Kiwi TCMS as tarball package inside Docker image instead of copying
  from the source directory
- Pylint fixes
- Remove ``testcases.views.ReturnActions()`` which is now unused
- Refactor New TestCase to class-based view and add tests



Kiwi TCMS 6.5 (1 Feb 2019)
--------------------------

We are celebrating 10 years of open source history at FOSDEM, Brussels!

**IMPORTANT:** this is a minor security, improvement and bug-fix update that
includes new versions of Django and other dependencies,
removes some database fields, includes backend API updates and
fixes several bugs.

Together with this release we announce:

* `kiwitcms-tap-plugin <https://github.com/kiwitcms/tap-plugin>`_ : for reading
  Test Anything Protocol (TAP) files and uploading the results to Kiwi TCMS
* `kiwitcms-junit.xml-plugin <https://github.com/kiwitcms/junit.xml-plugin>`_ :
  for reading junit.xml formatted files and uploading the results to Kiwi TCMS

Both of these are implemented in Python and should work on standard TAP and
junit.xml files generated by various tools!

Additionally 3 more plugins are currently under development by contributors:

* Native `JUnit 5 plugin <https://github.com/kiwitcms/junit-plugin/>`_ written
  in Java
* Native `PHPUnit <https://github.com/kiwitcms/phpunit-plugin/>`_ written
  in PHP
* `py.test plugin <https://github.com/kiwitcms/pytest-plugin/>`_


Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Security
~~~~~~~~

- Better override of SimpleMDE markdown rendering to prevent XSS
  vulnerabilities in SimpleMDE


Improvements
~~~~~~~~~~~~

- Update patternfly to version 3.59.1
- Update bleach from 3.0.2 to 3.1.0
- Update django-vinaigrette from 1.1.1 to 1.2.0
- Update django-simple-history from 2.6.0 to 2.7.0
- Update django-grappelli from 2.12.1 to 2.12.2
- Update mysqlclient from 1.3.14 to 1.4.1
- Update psycopg2 from 2.7.6.1 to 2.7.7
- Update pygithub from 1.43.4 to 1.43.5
- Convert TestCase page to Patternfly

  - page menu is under ``...`` in navigation bar
  - Test plans card is missing the old 'add plan' functionality b/c we are not
    at all sure if adding plans to test cases is used at all. Can bring it back
    upon user request!
  - Bugs card is missing the add/remove functionality for b/c we are not
    quite sure how that functionality is used outside test runs!
- Convert new TestCase page to Patternfly and provide Given-When-Then text
  template. This prompts the author to use a BDD style definition for their
  scenarios. We believe this puts the tester into a frame of mind more
  suitable for expressing what needs to be tested
- Add a favicon. Fixes
  `Issue #532 <https://github.com/kiwitcms/Kiwi/issues/532>`_
- Sort Component, Product and Version objects alphabetically. Fixes
  `Issue #633 <https://github.com/kiwitcms/Kiwi/issues/633>`_
- Search test case page now shows Components and Tags
- Search test case page now allows filtering by date. Fixes
  `Issue #715 <https://github.com/kiwitcms/Kiwi/issues/715>`_
- Search test case page now uses radio buttons to filter by automation status
- Small performance improvement when searching test plans and test cases
- Search test run page now allows to filter by Product but still continue to
  display all Builds in the selected Product
- Updated doc-string formatting for some ``tcms`` modules


Database migrations
~~~~~~~~~~~~~~~~~~~

**Known issues:** on our demo installation we have observed that permission
labels were skewed after applying migrations. The symptom is that labels for
removed models are still available, labels for some models may have been
removed
from groups/users or there could be permission labels appearing twice in the
database.

This may affect only existing installations, new installations do not have
this problem!

We are not certain what caused this but a quick fix is to remove all
permissions from the default *Tester* group and re-add them again!

- Remove ``TestCase.alias``
- Remove ``TestCaseRun.running_date``
- Remove ``TestCaseRun.notes``
- Remove ``TestCase.is_automated_proposed``
- Remove ``TestCaseText`` model, merge into ``TestCase.text`` field. Closes
  `Issue #198 <https://github.com/kiwitcms/Kiwi/issues/198>`_
- Remove ``Priority.sortkey``
- Remove ``Build.description``
- Remove ``Classification.sortkey`` and ``Classification.description``
- Convert ``TestCase.is_automated`` from ``int`` to ``bool``
- Rename ``TestCaseRun.case_run_status`` to ``status``


API
~~~

- New method ``TestCaseRunStatus.filter()``
- New method ``Product.create()``
- New method ``Classification.filter()``
- New method ``BugSystem.filter()``
- Changes to ``TestCase.add_component()``:

  - now accepts component name instead of id
  - now fails if trying to add components linked to another Product.
  - now returns serialized ``TestCase`` object


Translations
~~~~~~~~~~~~

- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_


Bug fixes
~~~~~~~~~

- Fix for missing migrations from ``django-simple-history``, see
  `DSH #512 <https://github.com/treyhunner/django-simple-history/issues/512>`_ and
  `StackOverflow #54177838 <https://stackoverflow.com/questions/54177838/>`_
- Fix cloning of test cases by surrounding bootstrap-selectpicker call with
  ``try-catch``. Fixes
  `Issue #695 <https://github.com/kiwitcms/Kiwi/issues/695>`_
- Fix a traceback with TestRun report page when the RPC connection to Bugzilla
  can't be established


Refactoring
~~~~~~~~~~~

- Remove unused form classes, methods, fields and label attributes
- Remove unused or duplicate methods from ``TestCase`` model
- Remove useless methods from BaseCaseForm()
- Add test for discovering missing migrations
- Add test for sanity checking PyPI packages which will always
  build tarball and wheel packages



tcms-api 5.2 (30 Jan 2019)
--------------------------

- Add ``plugin_helpers.Backend`` which implements our test runner plugin
  `specification <http://kiwitcms.org/blog/atodorov/2018/11/05/test-runner-plugin-specification/>`_
  in Python
- Add dependency to ``kerberos`` (Aniello Barletta)



Kiwi TCMS 6.4 (7 Jan 2019)
--------------------------

**IMPORTANT:** this is a security, improvement and bug-fix update that
includes new versions of Django, Patternfly and other dependencies.

Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Security
~~~~~~~~

- Update Django from 2.1.4 to 2.1.5, which deals with CVE-2019-3498:
  Content spoofing possibility in the default 404 page
- Update Patternfly to version 3.59.0, which deals with XSS issue in bootstrap.
  See CVE-2018-14041
- By default session cookies will expire after 24 hours. This can be controlled
  via the ``SESSION_COOKIE_AGE`` setting. Fixes
  `Issue #556 <https://github.com/kiwitcms/Kiwi/issues/556>`_


Improvements
~~~~~~~~~~~~

- Update mysqlclient from 1.3.13 to 1.3.14
- Update python-gitlab from 1.6.0 to 1.7.0
- Update django-simple-history from 2.5.1 to 2.6.0
- Update pygithub from 1.43.3 to 1.43.4
- New API method ``TestCase.remove()``. Initially requested as
  `SO #53844380 <https://stackoverflow.com/questions/53844380/>`_
- Drop down select widges in Patternfly pages are now styled with
  ``bootstrap-select`` giving them more consistent look and feel with
  the rest of the page (Anton Sankov)
- Create new TestPlan page now includes toggles to control notifications
  and whether or not the test plan is active. This was previously available
  only in edit page (Anton Sankov)
- By default TestPlan notification toggles are turned on. Previously they
  were off (Anton Sankov)
- Create and Edit TestPlan pages now look the same (Anton Sankov)
- Kiwi TCMS is now accepting donations via
  `Open Collective <https://opencollective.com/kiwitcms>`_


Removed functionality
~~~~~~~~~~~~~~~~~~~~~

- Remove ``TestPlan page -> Run menu -> Add cases to run`` action.
  This is the same as ``TestRun page -> Cases menu -> Add`` action
- Legacy reports will be removed after 1st March 2019. Provide your
  feedback in
  `Issue #657 <https://github.com/kiwitcms/Kiwi/issues/657>`_
- The ``/run/`` URL path has been merged with ``/runs/`` due to configuration
  refactoring. This may break your bookmarks or permalinks!


Bug fixes
~~~~~~~~~

- Don't traceback if markdown text is ``None``. Originally reported as
  `SO #53662887 <https://stackoverflow.com/questions/53662887/>`_
- Show loading spinner when searching. Fixes
  `Issue #653 <https://github.com/kiwitcms/Kiwi/issues/653>`_
- Quick fix: when viewing TestPlan cases make TC summary link to the test case.
  Previously the summary column was a link to nowhere.


Translations
~~~~~~~~~~~~

- Updated `Chinese Traditional translation <https://crowdin.com/project/kiwitcms/zh-TW#>`_
- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_


Refactoring
~~~~~~~~~~~

- New and updated internal linters
- Refactor ``testplans.views.new`` to class based view (Anton Sankov)
- Refactor ``TestCase -> Bugs tab -> Remove`` to JSON-RPC. References
  `Issue #18 <https://github.com/kiwitcms/Kiwi/issues/18>`_
- Refactor ``removeCaseRunBug()`` to JSON-RPC, References
  `Issue #18 <https://github.com/kiwitcms/Kiwi/issues/18>`_
- Remove unused ``render_form()`` methods
- Remove unnecessary string-to-int conversion (Ivaylo Ivanov)
- Remove obsolete label fields. References
  `Issue #652 <https://github.com/kiwitcms/Kiwi/issues/652>`_ (Anton Sankov)
- Pylint fixes
- Remove JavaScript that duplicates ``requestOperationUponFilteredCases()``
- Remove ``QuerySetIterationProxy`` class - not used anymore



Kiwi TCMS 6.3 (4 Dec 2018) - Heisenbug Edition
----------------------------------------------

**IMPORTANT:** this is a medium severity security update that includes new
versions of Django and Patternfly, new database migrations,
lots of improvements, bug fixes and internal refactoring.

Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)

After upgrade don't forget to::

    ./manage.py migrate


Security
~~~~~~~~

- Resolve medium severity XSS vulnerability which can be exploited when
  previewing malicious text in Simple MDE editor. See
  `CVE-2018-19057 <https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2018-19057>`_,
  `SNYK-JS-SIMPLEMDE-72570 <https://snyk.io/vuln/SNYK-JS-SIMPLEMDE-72570>`_
- Use ``mozilla/bleach`` before rendering Markdown to the user as a second
  layer of protection against the previously mentioned XSS vulnerability.


Improvements
~~~~~~~~~~~~

- Update to `Django 2.1.4 <https://docs.djangoproject.com/en/2.1/releases/2.1.4/>`_
- Update to `Patternfly 3.58.0 <https://github.com/patternfly/patternfly/releases>`_
- Make docker container restartable (Maik Opitz, Adam Hall)
- Add GitLab issue tracker integration. Fixes
  `Issue #176 <https://github.com/kiwitcms/Kiwi/issues/176>`_
  (Filipe Arruda, Federal Institute of Pernambuco)
- Convert ``Create new TestPlan`` page to Patternfly (Anton Sankov)
- Upon successfull registration show the list of super-users in case new
  accounts must be activated manually. This can be the same or expanded
  version of the addresses in the ``ADMIN`` setting. Include super-users
  in email notifications sent via ``tcms.signals.notify_admins()``.
- Don't include ``admin/js/*.js`` files in templates when not
  necessary. Results in faster page load. Fixes
  `Issue #209 <https://github.com/kiwitcms/Kiwi/issues/209>`_
- Enable ``nl2br`` Markdown extension which allows newline characters
  to be rendered as ``<br>`` tags in HTML. Visually the rendered
  text will look closer to what you seen in the text editor. Fixes
  `Issue #623 <https://github.com/kiwitcms/Kiwi/issues/623>`_
- Use auto-complete for adding components to TestCase


Removed functionality
~~~~~~~~~~~~~~~~~~~~~

- Bulk-update of Category for selected TestCase(s) inside of
  TestPlan
- Bulk-update of Components for selected TestCase(s) inside of
  TestPlan
- Bulk-update of automated status for selected TestCase(s) inside of
  TestPlan
- Bulk-remove for TestCase Component tab

These actions have always been a bit broken and didn't check the
correct permission labels. You can still update items idividually!

- Selection of Components when creating new TestCase. Closes
  `Issue #565 <https://github.com/kiwitcms/Kiwi/issues/565>`_.
  Everywhere else Kiwi TCMS doesn't allow selection of many-to-many
  relationships when creating or editing objects. Tags, Bugs, Components,
  TestPlans can be added via dedicated tabs once the object has been saved.


Bug fixes
~~~~~~~~~

- Hide ``KiwiUserAdmin.password`` field from super-user. Fixes
  `Issue #610 <https://github.com/kiwitcms/Kiwi/issues/610>`_
- Don't show inactive Priority. Fixes
  `Issue #637 <https://github.com/kiwitcms/Kiwi/issues/637>`_
- Don't traceback when adding new users via Admin. Fixes
  `Issue #642 <https://github.com/kiwitcms/Kiwi/issues/642>`_
- Teach ``TestRun.update()`` API method to process the ``stop_date``
  field. Fixes
  `Issue #554 <https://github.com/kiwitcms/Kiwi/issues/554>`_ (Anton Sankov)
- Previously when reporting issues to Bugzilla, directly from a TestRun,
  Kiwi TCMS displayed the error ``Enable reporting to this Issue Tracker by
  configuring its base_url`` although that has already been configured.
  This is now fixed. See
  `Stack Overflow #53434949 <https://stackoverflow.com/questions/53434949/>`_


Database
~~~~~~~~

- Remove ``TestPlan.owner`` field, duplicates ``TestPlan.author``


Translations
~~~~~~~~~~~~

- Updated `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_


Refactoring
~~~~~~~~~~~

- Remove ``fmt_queries()``. Fixes
  `Issue #330 <https://github.com/kiwitcms/Kiwi/issues/330>`_ (Anton Sankov)
- Remove unused parameter from ``plan_from_request_or_none()``. Refers to
  `Issue #303 <https://github.com/kiwitcms/Kiwi/issues/303>`_ (Anton Sankov)
- Remove ``ComponentActions()`` class. Fixes
  `Issue #20 <https://github.com/kiwitcms/Kiwi/issues/20>`_
- Convert lots of AJAX calls to JSON-RPC
- Remove lots of unused Python, JavaScript and templates. Both after migration
  to JSON RPC and other leftovers
- Pylint fixes (Alexander Todorov, Anton Sankov)



Kiwi TCMS 6.2.1 (12 Nov 2018)
-----------------------------

**IMPORTANT:** this is a small release that includes some improvements
and bug-fixes

Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2 (or newer)


Improvements
~~~~~~~~~~~~

- Update to `Patternfly 3.57.0 <https://github.com/patternfly/patternfly/releases>`_
- Update to `psycopg2 2.7.6.1 <http://initd.org/psycopg/articles/tag/release/>`_

Bug fixes
~~~~~~~~~

- Fix InvalidQuery, field ``TestCase.default_tester`` cannot be both deferred and
  traversed using ``select_related`` at the same time. References
  `Issue #346 <https://github.com/kiwitcms/Kiwi/issues/346>`_

Refactoring
~~~~~~~~~~~

- Pylint fixes (Ivaylo Ivanov)
- Remove JavaScript and Python functions in favor of existing JSON-RPC
- Remove vendored-in ``js/lib/jquery.dataTables.js`` which is now replaced by
  the npm package ``datatables.net`` (required by Patternfly)


Translations
~~~~~~~~~~~~

- New `French translation <https://crowdin.com/project/kiwitcms/fr#>`_
  (Christophe CHAUVET)



Kiwi TCMS 6.2 (02 Nov 2018) - PiterPy Edition
---------------------------------------------

**IMPORTANT:** this is a small release that removes squashed migrations
from previous releases and includes a few improvements.

Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1
    6.1.1            -> 6.2


Improvements
~~~~~~~~~~~~

- Update to `Django 2.1.3 <https://docs.djangoproject.com/en/2.1/releases/2.1.3/>`_
- Update Apache config to print logs on the console. Fixes
  `Issue #549 <https://github.com/kiwitcms/Kiwi/issues/549>`_


Database
~~~~~~~~

- Remove old variants of squashed migrations from earlier releases


Translations
~~~~~~~~~~~~

- Updated `German translation <https://crowdin.com/project/kiwitcms/de#>`_


Refactoring
~~~~~~~~~~~

- Update ``tcms.tests.factories.BugFactory`` (Ivaylo Ivanov)
- Add test for ``tcms.testcases.views.group_case_bugs`` (Ivaylo Ivanov)
- Pylint fixes (Ivaylo Ivanov)
- Remove unused JavaScript and re-use the existing JSON RPC methods



Kiwi TCMS 6.1.1 (29 Oct 2018)
-----------------------------

**IMPORTANT:** this release squashes database migrations and removes
older migrations that have been squashed in previous releases, a few
improvements and bug fixes.

Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1
    6.1              -> 6.1.1


Improvements
~~~~~~~~~~~~

- Dashboard will now show TestRuns which have test cases assigned to current
  user. Fixes
  `Issue #520 <https://github.com/kiwitcms/Kiwi/issues/520>`_
- API method ``TestRun.add_case()`` now returns a serialized TestCaseRun
  object. Previously this method returned None


Bug fixes
~~~~~~~~~

- Don't show disabled Priority records in UI. Fixes
  `Issue #334 <https://github.com/kiwitcms/Kiwi/issues/334>`_


Translations
~~~~~~~~~~~~

- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_


Refactoring
~~~~~~~~~~~

- Fix some pylint errors (Ivaylo Ivanov)


Database
~~~~~~~~

- Remove old squashed migrations for ``management``, ``testplans``,
  ``testcases`` and ``testruns`` apps
- Squash the remaining migrations for ``management``, ``testplans``,
  ``testcases`` and ``testruns`` apps



Kiwi TCMS 6.1 (20 Oct 2018)
---------------------------

**IMPORTANT:** this release introduces new database migrations,
internal updates and bug fixes. It is a small release designed
to minimize the number of database migrations by squashing them together.

Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1
    6.0.1            -> 6.1


After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- New middleware that will check missing settings. At the moment will only
  check Base URL configuration which often gets forgotten!


Bug fixes
~~~~~~~~~

- Hot-fix for error caused by the API method ``TestRun.update``. Error was
  initially reported on
  `StackOverflow <https://stackoverflow.com/questions/52865463/>`_.
  This patch makes it possible to use the API without crashing however the
  ``TestRun.update`` method doesn't handle the ``stop_date`` field at the
  moment!


Translations
~~~~~~~~~~~~

- Updated translation source strings


Database
~~~~~~~~

- Squash migrations for ``management`` app
- Squash migrations for ``testcases`` app
- Squash migrations for ``testplans`` app
- Squash migrations for ``testruns`` app



Kiwi TCMS 6.0.1 (20 Oct 2018)
-----------------------------

**IMPORTANT:** this release introduces new database migrations and
internal updates. It is a small release designed
to minimize the number of database migrations by squashing them together.

Supported upgrade paths::

    5.3   (or older) -> 5.3.1
    5.3.1 (or newer) -> 6.0.1


After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update `Jira from 1.0.10 to 2.0.0 <https://github.com/pycontribs/jira>`_
- Update to `Patternfly 3.55.0 <https://github.com/patternfly/patternfly/releases>`_
- Use button instead of HTML link for deleting test plan (Oleg Kainov)


Translations
~~~~~~~~~~~~

- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_
- Updated `German translation <https://crowdin.com/project/kiwitcms/de#>`_
- Updated translation source strings


Refactoring
~~~~~~~~~~~

- Fix pylint errors (Ivaylo Ivanov)
- Remove unused ``TestRun.list`` and ``TestCase.list_confirmed`` methods
- Remove unused ``plan_by_id_or_name()`` and ``is_int()``. Fixes
  `Issue #269 <https://github.com/kiwitcms/Kiwi/issues/269>`_


Database
~~~~~~~~

- Rename ``tcms.core.contrib.auth`` to ``tcms.kiwi_auth``
- Remove field ``user`` from ``TestCaseTag``, ``TestRunTag`` and
  ``TestPlanTag`` models



Kiwi TCMS 6.0 (04 Oct 2018)
---------------------------

**IMPORTANT:** this release introduces new database migrations, removal of
environment properties in favor of tags, internal updates and bug fixes.
After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update to `Django 2.1.2 <https://docs.djangoproject.com/en/2.1/releases/2.1.2/>`_
  due to high severity security issue
- Update to `Patternfly 3.54.8 <https://github.com/patternfly/patternfly/releases>`_
- ``Tag`` objects are now shown in Admin panel
- Add autocomplete when adding tags to ``TestRun`` via UI


Removed functionality
~~~~~~~~~~~~~~~~~~~~~

- TestCase new and edit views no longer allow editing of tags. Tags can be
  added/removed from the Tags tab which also makes sure to properly account
  for permissions
- Remove ``EnvGroup``, ``EnvProperty`` and ``EnvValue`` models in favor of
  tags.
  Existing values and properties are converted into tags and automatically
  added to test runs!
- Convert squashed database migrations to regular ones and remove older
  migrations.
  **WARNING:** upgrade from versions <= 5.3.1 to 6.0 will break without an
  intermediate upgrade to ``kiwitcms/kiwi:5.3.1 a420465852be``.
- Remove deprecated ``TestCase.estimated_time`` and ``TestRun.estimated_time``. Fixes
  `Issue #514 <https://github.com/kiwitcms/Kiwi/issues/514>`_


Backend API
-----------

- No longer use ``product_version`` for ``TestRun.create``. Fixes
  `Issue #522 <https://github.com/kiwitcms/Kiwi/issues/522>`_

  - 'product' is no longer required
  - 'product_version' is no longer required
  - 'manager' and 'default_tester' can be usernames or IDs

- ``TestCase.create`` no longer accepts 'tag' values
- ``TestRun.add_tag`` and ``TestRun.remove_tag`` now return list of tags.
  Previously these methods returned ``None``!
  This is the list of tags assigned to the TestRun that is being modified!


Bug fixes
~~~~~~~~~

- Fix mismatched HTML tag in ``plan/get.html`` template (Oleg Kainov)
- Don't use ``|slugify`` filter in templates which breaks HTML links with non-ASCII
  TestPlan names. Fixes
  `Sentry KIWI-TCMS-38 <https://sentry.io/open-technologies-bulgaria-ltd/kiwi-tcms/issues/676626096/>`_


Refactoring
~~~~~~~~~~~

- Fix pylint errors (Ivaylo Ivanov, Anton Sankov)
- Use existing JSON-RPC methods to add/remove tags via webUI and remove
  specialized backend methods that handled these requests. Also make sure to
  obey respective permissions


Translations
~~~~~~~~~~~~

- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_



Kiwi TCMS 5.3.1 (04 Sept 2018)
------------------------------

Visual changes
~~~~~~~~~~~~~~

- Add pagination controls to pages with search results



Kiwi TCMS 5.3 (04 Sept 2018)
----------------------------

**IMPORTANT:** this release brings lots of UI updates and removal of unused
and/or duplicated functionality and source code. Many pages have been
redesigned with the Patternfly library to have a modern look and feel.

Kiwi TCMS is now using the
`'kiwi-tcms' <https://stackoverflow.com/questions/tagged/kiwi-tcms>`_
tag on StackOverflow to track questions.

This will be the last release to carry around squashed migrations. In version
6.0 older migrations will be deleted and upgrades from versions <=5.2 to 6.0
will break without an intermediate upgrade to 5.3! Use ``kiwitcms/kiwi:5.3.1``
from Docker Hub when upgrading at some point in the future!


After upgrade don't forget to::

    ./manage.py migrate


Improvements
~~~~~~~~~~~~

- Update to `Django 2.1.1 <https://docs.djangoproject.com/en/2.1/releases/2.1.1/>`_
- Update Patternfly version. Fixes
  `Issue #381 <https://github.com/kiwitcms/Kiwi/issues/381>`_
- Replace TinyMCE with SimpleMDE markdown editor. You may need to strip
  existing texts from HTML tags that were generated by TinyMCE
- Allow downstream builds to customize the login templates by
  providing ``registration/custom_login.html`` template. It can either
  override the entire login page or provide additional information inside
  the ``custom_login`` block!


Visual changes
~~~~~~~~~~~~~~

- Remove breadcrumbs at the top of pages. Only admin pages still have them
- Convert login and registration templates to Patternfly. Fixes
  `Issue #211 <https://github.com/kiwitcms/Kiwi/issues/211>`_
- Convert 404 and 500 templates to Patternfly
- Convert dashboard page to Patternfly
- Convert TestRun new, edit and clone pages to Patternfly. Fixes
  `Issue #17 <https://github.com/kiwitcms/Kiwi/issues/17>`_
- Convert Search Test Plans page to Patternfly
- Convert Search Test Runs page to Patternfly
- Convert Search Test Cases page to Patternfly
- TestPlan view page, Runs tab now re-uses the search form for test runs
  which is built using Patternfly


Removed functionality
~~~~~~~~~~~~~~~~~~~~~

- When creating or editing TestRun

  - field ``estimated_time`` is scheduled for removal and is not shown
  - ``product_version`` is scheduled for removal in favor of
    ``TR.plan.product_version``
  - Product & Version can't be edited anymore. Must be set on the parent
    TestPlan instead. Still allows to specify builds

- Remove the ability to clone multiple TestPlans from search results
- Remove the ability to upload TestPlan document files in favor of
  the existing API
- Remove TestCase export to XML in favor of existing API
- Remove Advanced Search functionality. Fixes
  `Issue #448 <https://github.com/kiwitcms/Kiwi/issues/448>`_,
  `Issue #108 <https://github.com/kiwitcms/Kiwi/issues/108>`_
- Remove tech preview feature: Django Report Builder


Translations
~~~~~~~~~~~~

- Updated `German translation <https://crowdin.com/project/kiwitcms/de#>`_
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_
- Marked more strings as translatable


Bug fixes
~~~~~~~~~

- Don't use ``get_full_url()`` where not needed. Closes
  `Issue #380 <https://github.com/kiwitcms/Kiwi/issues/380>`_
- Remove unused templates. Fixes
  `Issue #114 <https://github.com/kiwitcms/Kiwi/issues/114>`_
- Submit filter form when clicking on tag value. Fixes
  `Issue #426 <https://github.com/kiwitcms/Kiwi/issues/426>`_
- Update ``TestCaseRun.tested_by`` when setting status. Fixes
  `Issue #459 <https://github.com/kiwitcms/Kiwi/issues/459>`_
- Add tests for ``KiwiUserAdmin``. Closes
  `Issue #489 <https://github.com/kiwitcms/Kiwi/issues/489>`_


Settings
~~~~~~~~

- The following settings have been removed ``MOTD_LOGIN``, ``WELCOME_MESSAGE``
  and ``TINYMCE_DEFAULT_CONFIG``


Refactoring
~~~~~~~~~~~

- Fix pylint errors (Anton Sankov, Ivaylo Ivanov)
- Remove lots of unused functions and classes
- Remove old or unnecessary templates
- Remove ``html2text`` dependency
- Remove unused CSS and vendored-in JavaScript libraries
- Add JavaScript JSON-RPC client which is now used by the front-end to
  communicate with the existing JSON-RPC API on the back-end. This
  replaces many 'ajax' views which are only used to render the UI and were
  duplicating functionality with existing API
- Non ``dist/`` files are no longer removed from ``node_modules/`` when
  building a docker image because packages like ``moment.js`` and
  ``bootstrap-datetimepicker.js`` don't ship their files in ``dist/``
- Convert TestPlans.TreeView to JSON RPC



Kiwi TCMS 5.2 (07 August 2018)
------------------------------

**IMPORTANT:** this release introduces new database migrations and converts
the Docker image to a non-root user with uid 1001. You may have to adjust
ownership/permissions on the ``kiwi_uploads`` Docker volume! After upgrade
don't forget to::

    ./manage.py migrate


Enhancements
~~~~~~~~~~~~

- Upgrade to `Django 2.1 <https://docs.djangoproject.com/en/2.1/releases/2.1/>`_
- Upgrade to ``django-report-builder 6.2.2``, compatible with Django 2.1
- Docker image now executes with uid 1001 instead of root

  - image based on ``centos7`` image instead of ``centos/httpd``
  - image now exposes ports 8080 and 8443
  - Apache logs now printed on Docker console
  - SSL certificates copied to ``/Kiwi/ssl`` inside Docker image instead of
    being bind-mounted
  - uploads dir changed to ``/Kiwi/uploads``
  - static dir changed to ``/Kiwi/static``
  - ``/Kiwi`` is now owned by uid 1001
  - ``/venv`` is now owned by uid 1001
  - ``docker-compose.yml`` is updated to match
- Fix pylint errors (Ivaylo Ivanov)
- Allow users to see other profiles via Admin
- Use password change form from Admin instead of custom one
- ``product.py`` will try to import ``local_settings.py`` if available in the
  same directory. This can be used to customize settings in downstream
  distributions
- Updated `Slovenian translation <https://crowdin.com/project/kiwitcms/sl#>`_


Bug fixes
~~~~~~~~~

- Make password reset views public
- Don't crash when adding new users via Admin


Refactoring
~~~~~~~~~~~

- Remove ``UserProfile`` model. Kiwi TCMS doesn't needs extra information
  about users so we remove this part of the application. Custom installations
  may choose to define their own profiles if they wish
- Remove custom ``DBModelBackend`` authentication backend
- Remove unused ``tcms.core.context_processors.auth_backend_processor``
- Remove unused ``get_using_backend()``. Fixes
  `Issue #261 <https://github.com/kiwitcms/Kiwi/issues/261>`_
- Remove ``dj_pagination``. Fixes
  `Issue #110 <https://github.com/kiwitcms/Kiwi/issues/110>`_


Settings
~~~~~~~~~

- ``AUTHENTICATION_BACKENDS`` is removed
- ``PAGINATION_DEFAULT_PAGINATION`` is removed
- Navigation menu links are now defined in ``MENU_ITEMS`` and can be redefined


Signals
~~~~~~~

- ``USER_REGISTERED_SIGNAL`` now doesn't receive the ``backend`` parameter



Kiwi TCMS 5.1 (31 July 2018)
----------------------------

**IMPORTANT:** this release introduces new database migrations, an experimental
reporting feature, deprecated functionality and bug fixes. After upgrade don't
forget to::

    ./manage.py migrate


Enhancements
~~~~~~~~~~~~

- Integrate with Django Report Builder as tech-preview. This makes it possible
  for power users and administrators to generate
  `tabular reports <http://django-report-builder.readthedocs.io/en/latest/howto/>`_.
  You will have to know the existing DB schema if you want to create your own
  reports.
  See http://kiwitcms.readthedocs.io/en/latest/db.html. This feature is in
  tech-preview and it may be removed if it doesn't work out. Please comment at:
  `Issue #452 <https://github.com/kiwitcms/Kiwi/issues/452>`_.
- Allow using ``manage.py dumpdata|loaddata|sqlflush|dbshell`` for backups, see
  `blog post <http://kiwitcms.org/blog/atodorov/2018/07/30/how-to-backup-docker-volumes-for-kiwi-tcms/>`_
- In TestCase view page add a link to delete the current test case
- In TestCase Admin page the ``+ Add TestCase`` button now allows to create new
  test case
- The version menu item in the helper menu now links to
  `Changelog <https://github.com/kiwitcms/Kiwi/blob/master/CHANGELOG.rst#change-log>`_


Deprecated functionality
~~~~~~~~~~~~~~~~~~~~~~~~

- Start showing deprecation warning for Advanced search, see
  `Issue #448 <https://github.com/kiwitcms/Kiwi/issues/448>`_


Bug fixes
~~~~~~~~~

- Allows Product/Version/Build to be shown in Testing Report. Fixes
  `Sentry KIWI-TCMS-2C <https://sentry.io/open-technologies-bulgaria-ltd/kiwi-tcms/issues/618688608/>`_
- Default to ``https://`` links if not running locally. Fixes
  `Issue #450 <https://github.com/kiwitcms/Kiwi/issues/450>`_
- Apply missing CSS class for object history table so it can be displayed
  nicely


Refactoring
~~~~~~~~~~~

- Squash some database migrations
- Fix a number of pylint issues
- Remove unused ``testruns.views::view_caseruns()``. References
  `Issue #316 <https://github.com/kiwitcms/Kiwi/issues/316>`_
- Remove unused template ``report/caserun.html``
- Handle TestRun deletion via admin not home grown code



Kiwi TCMS 5.0 (24 July 2018)
----------------------------

**IMPORTANT:** this release introduces new database migrations, object history
tracking, removal of old functionality and unused code, lots of internal
updates and bug fixes. After upgrade don't forget to::

    ./manage.py migrate
    ./manage.py populate_history --auto

Settings
~~~~~~~~

- Remove ``CACHE`` because not used
- Remove ``PLAN_EMAIL_TEMPLATE``, ``CASE_EMAIL_TEMPLATE`` and
  ``CASE_DELETE_EMAIL_TEMPLATE``. Templates can still be overriden if desired

Enhancements
~~~~~~~~~~~~

- Upgrade to `Django 2.0.7 <https://docs.djangoproject.com/en/2.0/releases/2.0.7/>`_
- Allow to delete TestPlan. Fixes
  `Issue #273 <https://github.com/kiwitcms/Kiwi/issues/273>`_
- Don't include username in dashboard URL
- Copy latest TestPlan text when cloning
- Always require users to be logged in. Anonymous users will not be allowed
  access by default. Read-only access to some views
  (e.g. get TestPlan or TestRun)
  can be enabled by disabling ``GlobalLoginRequiredMiddleware``! Fixes
  `Issue #230 <https://github.com/kiwitcms/Kiwi/issues/230>`_
- Start tracking change history for TestPlan, TestCase, TestRun and
  TestCaseRun.
  Fixes `Issue #294 <https://github.com/kiwitcms/Kiwi/issues/294>`_
- History changes are recorded as unified diff which is a universally
  recognized format
- Show the actual changes in email notifications. Fixes
  `Issue #199 <https://github.com/kiwitcms/Kiwi/issues/199>`_

Bug fixes
~~~~~~~~~

- Fix ``UnboundLocalError local variable 'message' referenced before assignment``. Fixes
  `Sentry KIWI-TCMS-1S <https://sentry.io/open-technologies-bulgaria-ltd/kiwi-tcms/issues/589209883/>`_
- Make email address unique when adding users via admin panel. Fixes
  `Issue #352 <https://github.com/kiwitcms/Kiwi/issues/352>`_ and
  `Issue #68 <https://github.com/kiwitcms/Kiwi/issues/68>`_
- Fix ``unsupported operand type(s) for +=: 'int' and 'datetime.timedelta'`` by
  initializing timedelta variable properly. Fixes
  `Sentry KIWI-TCMS-1Y <https://sentry.io/open-technologies-bulgaria-ltd/kiwi-tcms/issues/593838484/>`_
- Remove ``core.models.fields`` with MySQL time conversions. Fixes
  `Issue #390 <https://github.com/kiwitcms/Kiwi/issues/390>`_
- Fix bad JavaScript comparison. Fixes Coverity #289956
- Remove expression with no effect. Fixes Coverity #289974
- Rewrite ``request_host_link()`` to fix Coverity #289987
- Fix Coverity #289923 - Typo in identifier
- Don't send emails for changes performed by myself. Fixes
  `Issue #216 <https://github.com/kiwitcms/Kiwi/issues/216>`_

Refactoring
~~~~~~~~~~~

- Fix pylint issues in several modules (Anton Sankov & Ivaylo Ivanov)
- Fix wrong Plan Type template variable in advanced search form
- Do not use ``Model.objects.update()`` because it doesn't respect history
- Use the standard ``ModelChoiceField`` instead of custom one
- Use ``updateRunStatus()`` instead of deprecated ``updateObject()``
- Simplify JavaScript function ``getInfo()`` and use it multiple times
- Simplify ``previewPlan()`` by removing unused parameters
- Unify ``addChildPlan()`` and ``removeChildPlan()``
- Unify ``getInfoAndUpdateObject()`` with ``changeCaseRunAssignee()``
- Unify ``onTestCaseStatusChange()`` with ``changeTestCaseStatus()``
- Convert ``TestCaseEmailSettings.cc_list`` to string field
- Merge ``report/caseruns_table.html`` with ``reports/caseruns.html``
- Rename model ``UserActivateKey`` to ``UserActivationKey``. Fixes
  `Issue #276 <https://github.com/kiwitcms/Kiwi/issues/276>`_
- Remove ``cached_entities()``. Fixes
  `Issue #307 <https://github.com/kiwitcms/Kiwi/issues/307>`_
- Remove ``TestPlanText.checksum`` field
- Remove checksum fields for ``TestCaseText`` model
- Remove unused and home-grown template tags
- Remove unused fields ``auto_blinddown``, ``description``, ``sortkey`` from
  ``TestCaseRunStatus`` model. Fixes
  `Issue #186 <https://github.com/kiwitcms/Kiwi/issues/186>`_
- Remove ``Meta.db_name`` effectively renaming all tables. New names will use
  Django's default naming scheme
- Remove RawSQL queries. We are now 100% ORM based. Fixes
  `Issue #36 <https://github.com/kiwitcms/Kiwi/issues/36>`_
- Remove duplicate ``MultipleEmailField`` definition
- Remove ``TCMSLog`` view, ``TCMSLogManager``, ``TCMSLogModel``
- Remove ``TestPlanText`` model, use ``TestPlan.text`` instead
- Remove unused JavaScript files
  - ``lib/detetmine_type.js``
  - ``lib/hole.js``
  - ``lib/scriptaculous-controls.js.patch``
  - ``lib/validations.js``
  - ``static/js/index.js``
- Remove ``constructPlanParentPreviewDialog()``
- Remove ``changeCasePriority()``
- Remove ``changeCaseRunOrder()``
- Remove ``debug_output()`` from JavaScript files
- Remove deprecated ``/ajax/update/`` end-point
- Remove ``taggleSortCaseRun()``
- Remove ``strip_parameters()``
- Remove ``_InfoObjects.users()``
- Remove ``get_value_by_type()``
- Remove ``testcases.views.get_log()``
- Remove ``mail_scene()`` methods and related templates


Removed functionality
~~~~~~~~~~~~~~~~~~~~~

- TestRun completion status is no longer updated automatically. You can still
  update the status manually via the 'Set Finished' or 'Set Running' links!
  Fixes `Issue #367 <https://github.com/kiwitcms/Kiwi/issues/367>`_
- Remove bookmarks functionality. There are many great bookmark manager apps
  and if the user is keen on bookmarks they should use one of them. Closes
  `Issue #67 <https://github.com/kiwitcms/Kiwi/issues/67>`_ and
  `Issue #210 <https://github.com/kiwitcms/Kiwi/issues/210>`_
- Don't track & display history of changes for ``EnvGroup`` model
- Remove Disable/Enable buttons from TestPlan page. Enabling and disabling
  can still be done via the edit page
- Remove ``changeParentPlan()`` and the ability to change TestPlan parents
  from the 'Tree View' tab. This can be done via the edit page
- When viewing a TestPlan the user is no longer able to specify a sorkey for a
  particular TestCase. Instead they can use the ``Re-order cases`` button and
  move around the entire row of cases to adjust the sort order
- When working with test case results, inside a TestRun you will not be allowed
  to change the order of execution. Order should be defined inside the TestPlan
  instead
- Remove ``XmlRpcLog()`` model. Kiwi TCMS will no longer log RPC calls to the
  database. This leads to a small performance boost and can be overriden on
  individual basis if you need to do so.

Translations
~~~~~~~~~~~~

- More source strings marked as translatable
- New translations for Chinese Simplified, Chinese Traditional,
  German and Slovenian
- Stop keeping compiled translations under git. Fixes
  `Issue #387 <https://github.com/kiwitcms/Kiwi/issues/387>`_


tcms-api 5.0 (24 July 2018)
---------------------------

- Requires Python 3.6 or newer because it fixes bugs related to Django's
  disabling of keep-alive connections. See https://bugs.python.org/issue26402
- The rpc client is now accessed via ``TCMS().exec.<Server-Method>``
- Leave only XML-RPC transport classes! This removes the top-level interface
  behind the API client and the consuming side is left to work with Python
  dictionaries instead of objects.
- Remove the interactive ``tcms`` script
- Remove ``tcms_api.config`` module
- Remove logging class
- Remove ``script_examples/`` directory. These were never tested and maintained



Kiwi TCMS 4.2 (23 June 2018)
----------------------------

**IMPORTANT:** this release introduces new database migrations,
security updates and GDPR related changes! It is also the first release after
a great deal of travelling for various conferences.

Security
~~~~~~~~

- Enable testing with Badit. Fixes
  `Issue #237 <https://github.com/kiwitcms/Kiwi/issues/237>`_
- Enable testing with
  `Coverity Scan <https://scan.coverity.com/projects/kiwitcms-kiwi>`_
- Enable testing with
  `pyup.io <https://pyup.io/repos/github/kiwitcms/Kiwi/>`_
- Enable testing with
  `Snyk <https://snyk.io/test/github/kiwitcms/Kiwi>`_
- Use SHA256 instead of MD5 and SHA1
- Use the ``secrets`` module for activation keys
- Remove unnecessary AJAX view that had remote code execution vulnerability
- Don't use hardcoded temporary directories
- Upgrade to
  `Patternfly 3.36.0 <https://github.com/patternfly/patternfly/releases/tag/v3.36.0>`_
  which fixes the following vulnerabilities:
  - https://snyk.io/vuln/npm:moment:20161019
  - https://snyk.io/vuln/npm:moment:20170905

Settings
~~~~~~~~

- ``BUGZILLA_AUTH_CACHE_DIR`` is a new setting that may be specified to control
  where Bugzilla auth cookies are saved! It is not specified by default and
  Kiwi TCMS uses a temporary directory each time we try to login into Bugzilla!

Enhancements
~~~~~~~~~~~~

- Upgrade to Python 3.6. Fixes
  `Issue #91 <https://github.com/kiwitcms/Kiwi/issues/91>`_
- Upgrade to `Django 2.0.6 <https://docs.djangoproject.com/en/2.0/releases/2.0.6/>`_
- Fix around 100 pylint issues (Anton Sankov)
- Update email confirmation template for newly registered users and make the
  text translatable
- Display ``Last login`` column in User admin page
- Add tests for ``tcms.management.views`` (Anton Sankov)
- Remove unused CSS selectors
- Remove unnecessary ``templates/comments/comments.html``

Bug fixes
~~~~~~~~~

- Remove unused deferred field ``product_version``. Fixes
  `Sentry KIWI-TCMS-1C <https://sentry.io/open-technologies-bulgaria-ltd/kiwi-tcms/issues/523948048/>`_
- Rename left-over ``get_url()`` to ``get_full_url()``. Fixes
  `Sentry KIWI-TCMS-1B <https://sentry.io/open-technologies-bulgaria-ltd/kiwi-tcms/issues/523855781/>`_
- Fix empty TestPlan url and Product fields in TestRun email notification. Fixes
  `Issue #353 <https://github.com/kiwitcms/Kiwi/issues/353>`_ (Matt Porter, Konsulko Group)

Translations
~~~~~~~~~~~~

- Updated translations for Chinese Simplified
- Updated translations for Chinese Traditional
- New language and translations for Slovenian

Documentation
~~~~~~~~~~~~~

- Added ``git clone`` command to documentation. Fixes
  `Issue #344 <https://github.com/kiwitcms/Kiwi/issues/344>`_ (Anton Sankov)

Models and database migrations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Increase checksum fields size to hold the new checksum values
- Increase ``activation_key`` field size to 64 chars

GDPR related
~~~~~~~~~~~~

- Allow users to delete their accounts. Link is present on ``My profile`` page.
  This will also delete any related objects using cascade delete
- Try not to be so obvious when it comes to displaying email addresses across
  the web interface. Instead show username and link to profile


tcms-api 4.2 (23 June 2018)
---------------------------

- Remove coloring. Fixes
  `Issue #185 <https://github.com/kiwitcms/Kiwi/issues/185>`_
- Fix using the API client against https URLs (Adam Łoszyn, Samsung)



Kiwi TCMS 4.1.4 (April 8 2018)
------------------------------


Enhancements
~~~~~~~~~~~~

- Upgrade to `Django 2.0.4 <https://docs.djangoproject.com/en/2.0/releases/2.0.4/>`_
- Enable pylint and fix around 700 issues (Anton Sankov)
- Add pylint plugin to check docstrings for triple double quotes. Fixes
  `Issue #296 <https://github.com/kiwitcms/Kiwi/issues/296>`_
- Add pylint plugin to check for list comprehensions. Fixes
  `Issue #270 <https://github.com/kiwitcms/Kiwi/issues/270>`_
- Add pylint plugin to check for class attributes enclosed with double
  underscores. These are dunders and are reserved for Python!


Signals
~~~~~~~

**BREAKING CHANGES**:

Renamed ``user_registered`` to ``USER_REGISTERED_SIGNAL`` and
``post_update`` to ``POST_UPDATE_SIGNAL``!


Bug fixes
~~~~~~~~~

- Change util function to default to https. Fixes
  `Issue #220 <https://github.com/kiwitcms/Kiwi/issues/220>`_
- Fix
  `Sentry KIWI-TCMS-17 <https://sentry.io/open-technologies-bulgaria-ltd/kiwi-tcms/issues/495015101/>`_
- Cast iterator to list. Fixes
  `Sentry KIWI-TCMS-19 <https://sentry.io/open-technologies-bulgaria-ltd/kiwi-tcms/issues/501200394/>`_
- Don't crash in Custom Report. Fixes
  `Sentry KIWI-TCMS-18 <https://sentry.io/open-technologies-bulgaria-ltd/kiwi-tcms/issues/499389305/>`_
- Better handling of TestPlan documents. Fixes
  `Sentry KIWI-TCMS-1A <https://sentry.io/open-technologies-bulgaria-ltd/kiwi-tcms/issues/501695244/>`_
- Fix sorting of entries in TestPlan -> Runs tab. Fixes
  `Sentry KIWI-TCMS-E <https://sentry.io/open-technologies-bulgaria-ltd/kiwi-tcms/issues/472757670/>`_


Refactoring
~~~~~~~~~~~

- Move Bugzilla and Kerberos backends code into their own repositories. Fixes
  `Issue #239 <https://github.com/kiwitcms/Kiwi/issues/239>`_
- Remove cache from TestCaseRunStatus. Fixes
  `Issue #279 <https://github.com/kiwitcms/Kiwi/issues/279>`_
- Rewrite ``UrlMixin``. Fixes
  `Issue #157 <https://github.com/kiwitcms/Kiwi/issues/157>`_ (Chenxiong Qi)
- Remove unused ``split_as_option`` template tag
- Internal refactoring and more tests in ``tcms/core/ajax.py``
- Delete unused file ``tcms/core/forms/widgets.py``
- Merge ``case/form/filter.html`` into ``plan/get_cases.html``
- Remove unused ``TestCaseStatus.id_to_string()``



Kiwi TCMS 4.1.3 (Mar 15 2018)
-----------------------------


Enhancements
~~~~~~~~~~~~

- Upgrade to `Django 2.0.3 <https://docs.djangoproject.com/en/2.0/releases/2.0.3/>`_
- Show ``date_joined`` column for user admin
- Expose httpd logs to the host running docker. Fixes
  `Issue #191 <https://github.com/kiwitcms/Kiwi/issues/191>`_


Bug fixes
~~~~~~~~~

- Move SSL keys under common directory in the container. Fixes
  `Issue #231 <https://github.com/kiwitcms/Kiwi/issues/231>`_

- Always select active builds for TestRun. Fixes
  `Issue #245 <https://github.com/kiwitcms/Kiwi/issues/245>`_
- Swap ``escape`` and ``escapejs`` filters. Fixes
  `Issue #234 <https://github.com/kiwitcms/Kiwi/issues/234>`_
- Globally disable ``delete_selected`` action in Admin, this removes the
  drop down selection widget! Fixes
  `Issue #221 <https://github.com/kiwitcms/Kiwi/issues/221>`_
- Fix error in TestCase view when ``from_plan`` is empty string. Fixes
  `Sentry KIWI-TCMS-Z <https://sentry.io/open-technologies-bulgaria-ltd/kiwi-tcms/issues/474369640/>`_
- Fix sorting issue when None is compared to int. Fixes
  `Sentry KIWI-TCMS-V <https://sentry.io/open-technologies-bulgaria-ltd/kiwi-tcms/issues/473996504/>`_
- Validate form field as integer, not char. Fixes
  `Sentry KIWI-TCMS-W <https://sentry.io/open-technologies-bulgaria-ltd/kiwi-tcms/issues/474058623/>`_
- [docs] Remove information about importing test cases via XML.
  This functionality was removed in version 3.49



Refactoring
~~~~~~~~~~~

- Refactor inner class ``CaseActions``. Fixes
  `Issue #21 <https://github.com/kiwitcms/Kiwi/issues/21>`_ (Chenxiong Qi)
- Only use ``get_cases.html`` template. Fixes
  `Issue #176 <https://github.com/kiwitcms/Kiwi/issues/176>`_
- Unify ``get_details_review.html`` and ``get_details.html`` templates
- Remove internal ``Prompt.render`` class and replace with Django messages
- Remove ``mail/delete_plan.txt`` template
- Remove ``handle_emails_pre_plan_delete`` signal handler
- Remove the ``Export`` button from TestPlan view, use Case->Export sub-menu
  item in the Cases tab. Also remove the export buttons from search and
  advanced search result templates. If you'd like to export the cases from
  a given plan you have to open it in a new browser window and use the menu
- Remove the ``Print`` button from plan search form
- Remove TestRun cloning from search results and plan details, use sub-menu
- Remove unnecessary JavaScript handling for EnvGroup edit view


Settings
~~~~~~~~

- Remove ``PLAN_DELELE_EMAIL_TEMPLATE`` setting (not used)


Models and database migrations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Use Django's own DurationField, instead of custom one. Fixes
  `Issue #183 <https://github.com/kiwitcms/Kiwi/issues/183>`_.
  API clients must now send values for ``estimated_time`` which must be in a
  format that ``parse_duration()`` understands, for example 'DD HH:MM:SS'! See
  https://docs.djangoproject.com/en/2.0/ref/utils/#django.utils.dateparse.parse_duration

**IMPORTANT:** this release introduces new database migrations!



Kiwi TCMS 4.1.0 (Feb 21 2018)
-----------------------------

Enhancements and bug fixes
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Add tests for ``tcms.core.ajax.tag`` (Anton Sankov)
- Remove unused code from ``tcms.core.ajax.tag`` (Anton Sankov)
- Refactor ``tcms.core.ajax.tag`` to work with only one object. Fixes
  `Issue #135 <https://github.com/kiwitcms/Kiwi/issues/135>`_ (Anton Sankov)
- Add test for tcms_api.TestRun. Closes
  `Issue #194 <https://github.com/kiwitcms/Kiwi/issues/194>`_
- Send the ``user_registered`` signal when new users are registered
- Add signal handler to notify admins on new users. Fixes
  `Issue #205 <https://github.com/kiwitcms/Kiwi/issues/205>`_
- Add ``is_superuser`` column to User admin. Fixes
  `Issue #206 <https://github.com/kiwitcms/Kiwi/issues/206>`_
- Properly pass variables to blocktrans tag. Fixes
  `Issue #225 <https://github.com/kiwitcms/Kiwi/issues/225>`_
- Minor documentation updates

Refactoring
~~~~~~~~~~~

- Remove double thread when sending email on ``post_save`` signal
- Remove unused ``EmailBackend`` authentication backend
- Remove unused ``tcms.core.models.signals``
- Consolidate all signals and handlers in ``tcms.signals``
- Make use of ``django_messages`` during account registration

Settings
~~~~~~~~

- Remove ``LISTENING_MODEL_SIGNAL`` (internal setting)
- New setting ``AUTO_APPROVE_NEW_USERS``. Fixes
  `Issue #203 <https://github.com/kiwitcms/Kiwi/issues/203>`_


Models and database migrations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Remove unused fields from ``Product`` model:
  ``disallow_new``, ``max_vote_super_bug``, ``vote_super_user``,
  ``field votes_to_confirm``, ``default_milestone``, ``milestone_url``
- Remove unused ``Milestone`` model


**IMPORTANT:** this release introduces new database migrations!



Kiwi TCMS 4.0.0 (Feb 10 2018)
-----------------------------

Enhancements and bug fixes
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Upgrade to Django 2.0.2
- Pin JIRA client version to 1.0.10. Fixes
  `Issue #195 <https://github.com/kiwitcms/Kiwi/issues/195>`_
- Generate api-docs for model classes
- Updated documentation for all RPC methods
- Use Grappelli jQuery initialization, fixes popup windows
- Unify RPC namespaces, API client class names and server-side model names.
  Fixes `Issue #153 <https://github.com/kiwitcms/Kiwi/issues/153>`_

Settings
~~~~~~~~

- Remove ``ADMIN_PREFIX`` setting

RPC methods refactoring
~~~~~~~~~~~~~~~~~~~~~~~

.. warning::

    This is not compatible with older tcms-api releases!

- Remove ``Build.check_build``, use ``Build.filter``
- Remove ``Build.get``, use ``Build.filter``
- Remove ``Build.get_caseruns``, use ``TestCaseRun.filter``
- Remove ``Build.get_runs``, use ``TestRun.filter``

- Rename ``Env.filter_groups``, use ``Env.Group.filter``
- Rename ``Env.filter_properties``, use ``Env.Property.filter``
- Rename ``Env.filter_values``, use ``Env.Value.filter``

- Remove ``Product.add_component``, use ``Component.create``
- Remove ``Product.add_version``, use ``Version.create``
- Remove ``Product.check_category``, use ``Category.filter``
- Remove ``Product.check_component``, use ``Component.filter``
- Remove ``Product.check_product``, use ``Product.filter``
- Remove ``Product.filter_categories``, use ``Category.filter``
- Remove ``Product.filter_components``, use ``Component.filter``
- Remove ``Product.filter_versions``, use ``Version.filter``
- Remove ``Product.get``, use ``Product.filter``
- Remove ``Product.get_builds``, use ``Build.filter``
- Remove ``Product.get_cases``, use ``TestCase.filter``
- Remove ``Product.get_categories``, use ``Category.filter``
- Remove ``Product.get_category``, use ``Category.filter``
- Remove ``Product.get_component``, use ``Component.filter``
- Remove ``Product.update_component``, use ``Component.update``

- Rename ``Tag.get_tags`` to ``Tag.filter``



- Remove ``TestCase.add_comment``
- Update signature for ``TestCase.add_component``
- Update signature for ``TestCase.add_tag``
- Remove ``TestCase.add_to_run``, use ``TestRun.add_case``
- Remove ``TestCase.attach_bug``, use ``Bug.create``
- Remove ``TestCase.calculate_average_estimated_time``
- Remove ``TestCase.calculate_total_estimated_time``
- Remove ``TestCase.check_case_status``, use ``TestCaseStatus.filter``
- Remove ``TestCase.check_priority``, use ``Priority.filter``
- Update signature for ``TestCase.create``, no longer accepts ``plan``,
  ``component`` and ``bug`` dict attributes. Instead use
  ``TestPlan.add_case``, ``TestCase.add_component`` and ``Bug.create``
- Remove ``TestCase.detach_bug``, use ``Bug.remove``
- Remove ``TestCase.filter_count``
- Remove ``TestCase.get``, use ``TestCase.filter``
- Remove ``TestCase.get_bugs``, use ``Bug.filter({'case': ?})``
- Remove ``TestCase.get_bug_systems``
- Remove ``TestCase.get_case_status``, use ``TestCaseStatus.filter``
- Update signature for ``TestCase.get_components``
- Remove ``TestCase.get_plans``, use ``TestPlan.filter({'case': ?})``
- Remove ``TestCase.get_priority``, use ``Priority.filter``
- Remove ``TestCase.get_tags``, use ``Tag.filter({'case': ?})``
- Remove ``TestCase.get_text``, use ``TestCase.filter``
- Remove ``TestCase.link_plan``, use ``TestPlan.add_case``
- Rename ``TestCase.notification_add_cc`` to ``TestCase.add_notification_cc``
  and update signature
- Rename ``TestCase.notification_get_cc_list`` to
  ``TestCase.get_notification_cc``
  and update signature
- Rename ``TestCase.notification_remove_cc`` to
  ``TestCase.remove_notification_cc``
  and update signature
- Update signature for ``TestCase.remove_component``
- Update signature for ``TestCase.remove_tag``
- Remove ``TestCase.store_text``, use ``TestCase.update`` with
  ``setup``, ``breakdown``, ``action`` and ``effect`` attributes in the
  parameter dict
- Remove ``TestCase.unlink_plan``, use ``TestPlan.remove_case``

- Remove ``TestCasePlan.get``
- Remove ``TestCasePlan.update``

- Update ``TestCaseRun.add_comment`` to accept a single ID as first parameter
- Remove ``TestCaseRun.attach_bug``, use ``Bug.create``
- Rename ``TestCaseRun.attach_log`` to ``TestCaseRun.add_log``
- Remove ``TestCaseRun.detach_bug``, use ``Bug.remove``
- Rename ``TestCaseRun.detach_log`` to ``TestCaseRun.remove_log``
- Remove ``TestCaseRun.get``, use ``TestCaseRun.filter``
- Remove ``TestCaseRun.get_bugs``, use ``Bug.filter({'case_run': ?})``
- Remove ``TestCaseRun.get_case_run_status_by_name``
- Update signature for ``TestCaseRun.update``

- Remove ``TestPlan.add_component``
- Update signature for ``TestPlan.add_tag``
- Remove ``TestPlan.check_plan_type``, use ``PlanType.filter``
- Remove ``TestPlan.filter_count``
- Remove ``TestPlan.get``, use ``TestPlan.filter``
- Remove ``TestPlan.get_all_cases_tags``
- Remove ``TestPlan.get_components``
- Remove ``TestPlan.get_env_groups``, use ``Env.Group.filter({'testplan': ?})``
- Remove ``TestPlan.get_plan_type``, use ``PlanType.filter``
- Remove ``TestPlan.get_product``, use ``Product.filter({'plan': ?})``
- Remove ``TestPlan.get_tags``, use ``Tag.filter({'plan': ?})``
- Remove ``TestPlan.get_test_cases``, use ``TestCase.filter({'plan': ?})``
- Remove ``TestPlan.get_test_runs``, use ``TestRun.filter({'plan': ?})``
- Remove ``TestPlan.get_text``, use ``TestPlan.filter``
- Rename ``TestPlan.link_env_value`` to ``TestPlan.add_env_value``
  and update signature
- Remove ``TestPlan.remove_component``
- Update signature for ``TestPlan.remove_tag``
- Remove ``TestPlan.store_text``, use ``TestPlan.update`` with
  a ``text`` attribute in the parameter values
- Rename ``TestPlan.unlink_env_value`` to ``TestPlan.remove_env_value``
  and update signature
- Rename ``TestRun.add_cases`` to ``TestRun.add_case`` and update signature
- Update signature for ``TestRun.add_tag``
- Update signature for ``TestRun.create``, no longer accepts ``case``
  dict attribute. Instead use ``TestRun.add_case``
- Remove ``TestRun.filter_count``
- Remove ``TestRun.get``, use ``TestRun.filter``
- Remove ``TestRun.get_bugs``
- Remove ``TestRun.get_env_values``, use ``Env.Value.filter({'testrun': ?})``
- Remove ``TestRun.get_tags``, use ``Tag.filter({'run': ?})``
- Rename ``TestRun.get_test_cases`` to ``TestRun.get_cases``
- Remove ``TestRun.get_test_case_runs``, use ``TestCaseRun.filter({'run': ?})``
- Remove ``TestRun.get_test_plan``, use ``TestPlan.filter({'run': ?})[0]``
- Rename ``TestRun.remove_cases`` to ``TestRun.remove_case`` and update
  signature
- Update signature for ``TestRun.remove_tag``
- Update signature for ``TestRun.update``

- Rename ``User.get`` to ``User.filter``
- Rename ``User.join`` to ``User.join_group``
- Update signature for ``User.update``


Models and database migrations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Remove model ``TestEnvironment``
- Remove model ``TestEnvironmentCategory``
- Remove model ``TestEnvironmentElement``
- Remove model ``TestEnvironmentMap``
- Remove model ``TestEnvironmentProperty``
- Remove model ``TestPlanComponent``
- Remove ``TestPlan.get_text_with_version()``
- Remove ``TestRun.get_previous_or_next()``

**IMPORTANT:** this release introduces new database migrations!


tcms-api 4.0.0 (Feb 10 2018)
----------------------------

.. warning::

    This is not compatible with older XML-RPC versions!

- **Make the code compatible with Kiwi TCMS XML-RPC v4.0.0**
- Rename ``Status`` to ``TestCaseRunStatus``
- Rename ``CaseRun`` to ``TestCaseRun``
- Remove ``PlanStatus``, use ``TestPlan.is_active``
- Remove ``RunStatus``, use ``TestRun.finished``
- Remove ``TestPlan.components`` container
- Update signature for ``TestPlan``. Now accept ``text`` kwarg in constructor
  instead of ``document``.



Kiwi TCMS 3.50 (Jan 24 2018)
----------------------------

Enhancements and bug fixes
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Update documentation for XML-RPC and positional arguments, translations,
  environment groups
- Enable translations. Fixes
  `Issue #129 <https://github.com/kiwitcms/Kiwi/issues/129>`_
- Register models for DB translations. Fixes
  `Issue #182 <https://github.com/kiwitcms/Kiwi/issues/182>`_
- New German translations (@xbln)
- Require django-attachments>=1.3 and restore attachments count in tabs
- Fix missing tag names in TestPlan page
- Hide admin forms for some models not supposed to be editted by users. Fixes
  `Issue #174 <https://github.com/kiwitcms/Kiwi/issues/174>`_
- Use django-grappelli for the admin templates: modern look and feel and
  less template files overriden by Kiwi TCMS
- Load values for default property in TestRun 'Add Property' dialog. Fixes
  `Issue #142 <https://github.com/kiwitcms/Kiwi/issues/142>`_
- Correctly find property ID when renaming environment properties. Fixes
  `Issue #167 <https://github.com/kiwitcms/Kiwi/issues/167>`_
- Convert request body to string. Fixes
  `Issue #177 <https://github.com/kiwitcms/Kiwi/issues/177>`_

Refactoring
~~~~~~~~~~~

- Remove batch tag Add/Remove sub-menu in TestPlan view (Anton Sankov)
- Remove Edit tag button in Tag tab (Anton Sankov)
- Remove template functions. Fixes
  `Issue #107 <https://github.com/kiwitcms/Kiwi/issues/107>`_
- Remove custom HttpJSONResponse classes
- Remove unused and duplicate code


tcms-api 1.5.1 (Jan 24 2018)
----------------------------

- [api] Fix order of TestCaseRun statuses. Fixes #184


Kiwi TCMS 3.49 (Jan 02 2018)
----------------------------

Enhancements and bug fixes
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Upgrade to Django 2.0.1
- Don't log passwords sent via RPC
- Log XML-RPC requests from anonymous users. Fixes
  `Issue #126 <https://github.com/kiwitcms/Kiwi/issues/126>`_
- Order ``TCMSEnvValue`` records by property name and value. Fixes
  `Issue #155 <https://github.com/kiwitcms/Kiwi/issues/155>`_
- flake8 fixes (Anton Sankov)
- Start building source code documentation from Python doc strings
- Properly urlencode emails in personal menu links
- Remove test case import via XML files
- Use django-attachments for user uploaded files. Fixes
  `Issue #160 <https://github.com/kiwitcms/Kiwi/issues/160>`_
  As part of this change we no longer copy Plan and Case attachments when
  cloning these objects.

  NOTE: Since django-attachments introduces new permission objects
  you will have to adjust default permissions for existing users!
  In order for them to be able to upload/delete their own files they
  need to have ``attachments.add_attachment`` and
  ``atachments.delete_attachment`` permissions.

  These same permissions are added by default to the 'Tester' group.
  If you are running an existing installation registering a new user
  with Kiwi TCMS will update the default permissions for this group!

Refactoring
~~~~~~~~~~~

- Remove unused class EditCaseNotifyThread (Chenxiong Qi)
- Remove model TestPlanActivity  (Chenxiong Qi)
- Remove many unused models and classes
- Execute tests via ``manage.py test`` and drop py.test dependency
- Remove useless ``TestTag.string_to_list`` method. Fixes
  `Issue #106 <https://github.com/kiwitcms/Kiwi/issues/106>`_
- Use ``settings.AUTH_USER_MODEL`` in ForeignKey definitions. Fixes
  `Issue #143 <https://github.com/kiwitcms/Kiwi/issues/143>`_

Settings
~~~~~~~~

- Rename ``EMAIL_FROM`` to ``DEFAULT_FROM_EMAIL``. Fixes
  `Issue #128 <https://github.com/kiwitcms/Kiwi/issues/128>`_
- Rename ``FILE_UPLOAD_DIR`` to ``MEDIA_ROOT``
- Rename ``MAX_UPLOAD_SIZE`` to ``FILE_UPLOAD_MAX_SIZE``
- New setting ``DELETE_ATTACHMENTS_FROM_DISK``
- Remove unused ``XMLRPC_TEMPLATE`` and ``TESTOPIA_XML_VERSION``

Server side API
~~~~~~~~~~~~~~~

- Migrate to ``django-modern-rpc`` and remove home-grown XML-RPC handling code.
  As part of this change the XML-RPC endpoint has been changed to
  ``/xml-rpc/``. There's also a new JSON-RPC endpoint at ``/json-rpc/``!
- ``Auth.login`` method now accepts positional parameters
  ``username, password`` instead of dict
- ``TestCaseRun.get`` method now accepts a query dict as parameter
- ``TestCaseRun.get_bugs`` method now accepts a query dict as parameter

- Remove ``Build.lookup_id_by_name``, ``Build.lookup_name_by_id`` RPC methods
- Remove ``Product.lookup_name_by_id``, ``Product.lookup_id_by_name``
  RPC methods
- Remove ``Product.get_components``, use ``Product.filter_components`` instead
- Remove ``Product.get_plans``, use ``TestPlan.filter`` instead
- Remove ``Product.get_runs``, use ``TestRun.filter`` instead
- Remove ``Product.get_tag``, use ``Tag.get_tags`` instead
- Remove ``Product.get_versions``, use ``Product.filter_versions`` instead
- Remove ``TestCaseRun.filter_count``, use ``TestCaseRun.filter`` instead
- Remove ``TestCaseRun.get_s``, use ``TestCaseRun.get`` instead
- Remove ``TestCaseRun.get_bugs_s``, use ``TestCaseRun.get_bugs`` instead
- Remove ``TestCaseRun.get_case_run_status``, use
  ``TestCaseRun.get_case_run_status_by_name`` instead
- Remove ``TestCaseRun.get_completion_time``,
  ``TestCaseRun.get_completion_time_s``
  RPC methods. Instead calculate them on the client side
- Rename ``TestCaseRun.check_case_run_status`` to
  ``TestCaseRun.get_case_run_status_by_name``
- ``TestCaseRun.detach_log`` will not raise exceptions when deleting logs from
  non-existing TestCaseRun objects.
- Remove ``User.get_me``, instead use ``User.get`` without parameters
- Remove ``Version.`` and ``Testopia.`` RPC modules
- Update documentation for RPC methods in ``Auth``, ``Build`` and ``Env``
  namespaces. Unformatted documentation is also available for the rest of the
  RPC methods

**IMPORTANT:** this release introduces new database migrations!


tcms-api 1.5.0 (Jan 02 2018)
----------------------------

- Update endpoint configuration, compatible with Kiwi TCMS 3.49
- Drop support for Python 2
- Remove the internal ``do_command`` method which eliminates use of ``eval()``
- Remove ``TCMSXmlrpc.get_me()`` and ``TCMSXmlrpc.build_get()`` methods


3.48 (Nov 28 2017)
------------------

- Update to Django 1.11.7 (Mr. Senko)
- Update documentation including high level information
  about how data is organized within Kiwi TCMS and how to work
  with the system. (Mr. Senko)
- Stop caching report views. (Mr. Senko)
- Make test execution comments optional. Fixes
  `Issue #77 <https://github.com/MrSenko/Kiwi/issues/77>`_. (Mr. Senko)
- Escape special symbols when exporting JSON.
  Fixes `Issue #78 <https://github.com/MrSenko/Kiwi/issues/78>`_. (Mr. Senko)
- Remove Test Run export to XML functionality in favor of API.
  Fixes `Issue #79 <https://github.com/MrSenko/Kiwi/issues/79>`_. (Mr. Senko)
- Make it possible to search Test Runs via Env properties.
  Fixes `Issue #82 <https://github.com/MrSenko/Kiwi/issues/82>`_. (Mr. Senko)
- Display Environment properties in Test Run search results. (Mr. Senko)
- Allow bulk update TestCase.default_tester via email.
  Fixes `Issue #85 <https://github.com/MrSenko/Kiwi/issues/85>`_. (Mr. Senko)
- Don't crash reports when there are untested TestCaseRuns.
  Fixes `Issue #88 <https://github.com/MrSenko/Kiwi/issues/88>`_. (Mr. Senko)
- Bind localhost:80 to container:80.
  Fixes `Issue #99 <https://github.com/MrSenko/Kiwi/issues/99>`_. (Mr. Senko)
- Enable testing with Python 3.6 in preparation for migration. (Mr. Senko)
- If JIRA isn't fully configured then don't connect. Fixes
  Fixes `Issue #100 <https://github.com/MrSenko/Kiwi/issues/100>`_. (Mr. Senko)
- Pin patternfly version to 3.30 and update templates.
  Fixes `Issue #120 <https://github.com/MrSenko/Kiwi/issues/120>`_. (Mr. Senko)
- Show status name rather than status id in TestCaseRun change log.
  (Chenxiong Qi)
- [api] Adds a Python API client with changes that make it possible to
  execute on both Python 2 and Python 3. For now take a look at
  ``tcms_api/script_examples/`` for examples how to use it.
  NOTE: API client has been initially developed as the *python-nitrate*
  project by Petr Splichal and other contributors.
- [api] Remove experimental support for Teiid. (Mr. Senko)
- [api] Cache level defaults to ``CACHE_NONE`` if not set. (Mr. Senko)
- [api] Remove persistent cache, in-memory caching is still available.
  (Mr. Senko)
- [api] Remove multicall support. (Mr. Senko)


IMPORTANT: this release introduces new database migrations!


3.44 (Oct 31 2017)
------------------

- Use correct django_comment permission name. Allows non-admin users to enter
  comments. Fixes `Issue #74 <https://github.com/MrSenko/Kiwi/issues/74>`_. (Mr. Senko)
- Fix 500 ISE when viewing other user profiles (Mr. Senko)
- Add a more visible link to account registration in the MOTD section
  of the login page (Mr. Senko)
- Use correct permission names when editing Test Plan Environment Group field.
  Fixes `Issue #73 <https://github.com/MrSenko/Kiwi/issues/73>`_ (Mr. Senko)
- Update how we render the XMLRPC info page. Fixes
  `Issue #80 <https://github.com/MrSenko/Kiwi/issues/80>`_ (Mr. Senko)
- Rename ``FOOTER_LINKS`` setting to ``HELP_MENU_ITEMS`` (Mr. Senko)
- Update documentation with new screenshots (Mr. Senko)
- Make documentation more clear on how to run Kiwi TCMS both in production
  and in local development mode. Fixes
  `Issue #89 <https://github.com/MrSenko/Kiwi/issues/89>`_ (Mr. Senko)


3.41 (Oct 09 2017, released on MrSenko.com)
-------------------------------------------

- Upon registration assign default group permissions if none set.
  Also by default make all users have the ``is_staff`` permission
  so they can add Products, Builds, Versions, etc. via the ADMIN menu
  (Mr. Senko)
- Add ``docker-compose.yml`` file (Mr. Senko)
- Update documentation (Mr. Senko)
- Remove unused plugins_support/ directory (Mr. Senko)
- Remove unused models in ``tcms.profiles``. The ``Profiles``,
  ``Groups`` and ``UserGroupMap`` models are removed because they are
  not used (Mr. Senko)
- Remove max_length=30 limitation for EmailField in RegistrationForm.
  Fixes `Issue #71 <https://github.com/MrSenko/Kiwi/issues/71>`_ (Mr. Senko)
- Display error messages on login form (Mr. Senko)
- Update main navigation to indicate login is required before creating
  Test Plan (Mr. Senko)

WARNING:

    MariaDB defaults are to use ``latin1`` as the default character set and
    collation.
    This will lead to 500 internal server errors when trying to save data which
    does not use ASCII characters. This is a limitation with the underlying
    CentOS/MariaDB docker image and a
    `solution <https://github.com/CentOS/CentOS-Dockerfiles/pull/146>`_
    has been proposed upstream.

    You can manually update your existing databases by using the following instructions::

        bash-4.2$ mysql -u root -p
        Enter password:

        MariaDB [(none)]> ALTER DATABASE kiwi CHARACTER SET utf8 COLLATE utf8_unicode_ci;
        Query OK, 1 row affected (0.00 sec)

        bash-4.2$ mysql -D kiwi -u root -p -B -N -e "SHOW TABLES" | awk '{print "ALTER TABLE", $1, "CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;"}' > /tmp/alter_charset.txt
        Enter password:

        bash-4.2$ cat /tmp/alter_charset.txt | mysql -D kiwi -u root -p
        Enter password:

    You can use the ``SHOW TABLE STATUS;`` query to see the current settings for your tables!


IMPORTANT: this release introduces new database migrations!


3.39 (Sep 27 2017, released on MrSenko.com)
-------------------------------------------

- Introduce modern UI elements using Patternfly library!
  Main navigation, login and password reset pages are
  currently implemented. NOTE: main navigation is placed
  inside an iframe to workaround issues with the legacy
  JavaScript on other pages. These will be fixed in the future
  and the iframe will be removed! (Mr. Senko)
- Piwik integration has been removed together with the following settings
  ``ENABLE_PIWIK_TRACKING``, ``PIWIK_SITE_ID``, ``PIWIK_SITE_API_URL``,
  ``PIWIK_SITE_JS_URL`` (Mr. Senko)
- ``USER_GUIDE_URL`` setting has been removed. You can specify this
  configuration directly in ``FOOTER_LINKS`` (Mr. Senko)
- Added missing templates and views for password reset functionality
  (Mr. Senko)
- Makefile updates and flake8 fixes (Mr. Senko)


3.38 (Sep 20 2017, released on MrSenko.com)
-------------------------------------------

- Bug fix: Test Case EDIT and CLONE buttons are now working again (Mr. Senko)
- More tests and better handling of input parameters when loading builds
  (Mr. Senko)
- Load more of the required JavaScript and CSS files for admin forms
  (Mr. Senko)


3.37 (Sep 12 2017, released on MrSenko.com)
-------------------------------------------

- Migrate to Python 3. Docker container uses Python 3.5 from
  SoftwareCollections.org (Mr. Senko)
- Docker container now uses self-signed HTTPS with options to specify custom
  certificates (Mr. Senko)
- Set MySQL mode to ``STRICT_TRANS_TABLES`` (Mr. Senko)
- Remove dependency on ``django-preserialize`` (Mr. Senko)
- Remove explicit dependency on ``six`` (Mr. Senko)
- Fix traceback while loading builds at test run creation (Mr. Senko)
- Populate product version when crating new Test Plan. Fixes
  `Issue #16 <https://github.com/MrSenko/Kiwi/issues/16>`_ (Mr. Senko)
- Initialize admin jQuery after jQuery has been loaded. Fixes a problem with
  popup windows not closing (Mr. Senko)
- Fix traceback when loading product versions if no products were
  defined (Mr. Senko)



3.33 (Aug 15 2017, released on MrSenko.com)
-------------------------------------------

- Update Django to 1.11.4 (Mr. Senko)
- Many other updates related to deprecated features in Django (Mr. Senko)
- Fix a bug where the tab menu Bugs -> Remove didn't remove bugs from
  the currently opened test run (Mr. Senko)
- Make use of versioned static files which helps users see updates to
  the JavaScript and CSS files which are cached inside the browser. Fixes
  `Issue #6 <https://github.com/MrSenko/Kiwi/issues/6>`_ (Mr. Senko)



3.32 (Aug 8 2017, released on MrSenko.com)
------------------------------------------

- Upgrade Django to 1.10.7 (Mr. Senko)
- Replace unmaintained django-pagination with dj-pagination. Fixes
  `Issue #48 <https://github.com/MrSenko/Kiwi/issues/48>`_ (Mr. Senko)
- When activating new accounts check the expiration date of activation
  keys. Previously this was not checked (Mr. Senko)
- Fix a traceback when showing Plan -> Tree View (Mr. Senko)
- Fixed an issue where `Prompt.render` was wrapped within `HttpResponse`
  causing DB connections to be closed after view functions have returned
  (Mr. Senko)
- Refactored responses for AJAX calls (Chenxiong Qi)

IMPORTANT: this release introduces new database migrations!


3.30 (Jul 27 2017, released on MrSenko.com)
-------------------------------------------

- Upgrade Django to 1.9.13 (Mr. Senko)
- Upgrade all other requirements to their latest versions (Mr. Senko)
- Fix bug in `class BlobField` where database engine is not examined
  correctly (Mr. Senko)
- Replace `SQLExecution` with ORM queries (Mr. Senko)
- Improve test assertions so they don't fail when database returns
  records in arbitrary order (Mr. Senko)

IMPORTANT: this release introduces new database migrations!


3.28 (Jul 11 2017, released on MrSenko.com)
-------------------------------------------

- Replace w3m cmd line tool with html2text. Fixes
  `Issue #7 <https://github.com/MrSenko/Kiwi/issues/7>`_ (Mr. Senko)
- Disable bug reporting if Issue Tracker base_url is empty (Mr. Senko)
- Don't link TC to Issue Trackers if required parameters not present.
  By default these are api_url, api_username and api_password. For GitHub
  they are base_url and api_password. Fixes
  `Issue #3 <https://github.com/MrSenko/Kiwi/issues/3>`_ (Mr. Senko)
- Don't add component to testcase if component already exists. Fixes
  `Issue #13 <https://github.com/MrSenko/Kiwi/issues/13>`_ (Mr. Senko)
- Add more tests (Chenxiong Qi)
- Replace deprecated ``request.REQUEST`` (Chenxiong Qi, Mr. Senko)


3.26 (Jun 27 2017, released on MrSenko.com)
-------------------------------------------

- Multiple replacements of deprecated ``request.REQUEST`` and more tests
  (Chenxiong Qi)
- Use the ``EMAIL_SUBJECT_PREFIX`` setting when sending emails (Mr. Senko)
- Document how to use an external email provider instead of SMTP with
  example for Amazon SES. Fixes
  `Issue #12 <https://github.com/MrSenko/Kiwi/issues/12>`_ (Mr. Senko)
- Remove the ``KIWI_BASE_URL`` configuration setting. The Administration
  Guide now includes a section called *Configure Kiwi’s base URL* which
  explains how to configure the base URL of your installation! (Mr. Senko)

IMPORTANT: this release introduces new database migrations!


3.24 (Jun 13 2017, released on MrSenko.com)
-------------------------------------------

- Removed dependency on Celery and django-celery. The following configuration
  settings have been removed: ``BROKER_URL``, ``CELERY_TASK_RESULT_EXPIRES``,
  ``CELERY_RESULT_BACKEND``, ``CELERYD_TIMER_PRECISION``,
  ``CELERY_IGNORE_RESULT``, ``CELERY_MAX_CACHED_RESULTS``,
  ``CELERY_DEFAULT_RATE_LIMIT`` (Mr. Senko)
- Refactoring of internal email sending capabilities. The following
  configuration settings have been removed:
  ``EMAILS_FOR_DEBUG`` (replaced by ``ADMINS``), ``ENABLE_ASYNC_EMAIL``
  (Mr. Senko)
- Removed integration with *Errata System* and ``ERRATA_URL_PREFIX`` setting.
  Fixes `Issue #15 <https://github.com/MrSenko/Kiwi/issues/15>`_ (Mr. Senko)
- Removed dependency on qpid-python and QPID integration which has been
  disabled for a long time and most likely not working. This removes the
  ``ENABLE_QPID`` setting as well.
- Removed dependency on kerberos with instructions how to add it back and
  enabled it if required (Mr. Senko)
- Removed dependency on Kobo. Fixes
  `Issue #5 <https://github.com/MrSenko/Kiwi/issues/5>`_ (Mr. Senko)
- Add missing integrations for JIRA. It is now possible to link failed
  Test Case(s) to JIRA Issues and Report new issues with pre-filled information
  from the test case! Fixes
  `Issue #2 <https://github.com/MrSenko/Kiwi/issues/2>`_ (Mr. Senko)
- Add more tests (Chenxiong Qi)
- Add integration with GitHub issues. Fixes
  `Issue #4 <https://github.com/MrSenko/Kiwi/issues/4>`_ (Mr. Senko)


IMPORTANT: this release introduces new database migrations!


3.23 (Jun 6 2017, released on MrSenko.com)
------------------------------------------

- Docker compose is now hosted at https://github.com/MrSenko/kiwi-docker
  with the ability to customize all settings and the Docker image itself
  (Mr. Senko)
- Trimmed down the contents of the Docker image - removed unnecessary RPM
  packages (Mr. Senko)


3.22 (May 31 2017, released on MrSenko.com)
-------------------------------------------

- Multiple refactorings of deprecated Django features (Mr. Senko)
- Added more tests (Chenxiong Qi)
- Replace deprecated XML2Dict with xmltodict. Fixes
  `Issue #10 <https://github.com/MrSenko/Kiwi/issues/10>`_ (Mr. Senko)
- Use mysqlclient instead of MySQL-python. Fixes
  `Issue #14 <https://github.com/MrSenko/Kiwi/issues/14>`_ (Mr. Senko)
- Make TestCase changelog display state changes using their names. Fixes
  `Issue #9 <https://github.com/MrSenko/Kiwi/issues/9>`_ (Mr. Senko)
- Multiple documentation improvements, including documentation of all
  configuration settings (Mr. Senko)


3.21.2 (May 26 2017, released on MrSenko.com)
---------------------------------------------

- Forked from https://github.com/Nitrate/Nitrate as a stand-alone project
- Future versions will be released under the name **Kiwi TCMS**
- ``NITRATE_BASE_URL`` has been renamed to ``KIWI_BASE_URL``
- Use ``/tmp/.bugzilla`` for python-bugzilla cache to avoid 500 ISE


3.8.18.21 (May 24 2017, released on MrSenko.com)
------------------------------------------------

- Rebased onto f7e2c6c
- Includes PRs #197, #198, #199, #200, #201, #202, #204:
  removal of deprecated ``request.REQUEST`` and more tests (tkdchen)
- Includes PR #203: Minor fixes (Mr. Senko)
- Fixed failing test cases on PostgreSQL and MySQL (Mr. Senko)
- Remove unused doctest. PR #205 (tkdchen)
- Fixes Issue #185: Improve integrations between Nitrate and
  external bug tracking systems (Mr. Senko). In particular:

  - removed all hard-coded issue tracker settings
  - allow issue trackers to be configured entirely in the DB
  - re-implemented the functionality to open all bugs inside
    the issue tracker by clicking a single link at the bottom
    of the test run reports page
  - re-implemented the "Check to add test case(s) to Issue Tracker"
    checkbox when adding a bug to a test case run
  - re-implemented the "Report" bug functionality, which will pre-load
    the chosen Issue Tracker with information about the test case
    which was used to discover the bug.
  - NOTE: full integration is available only for Bugzilla. This version
    provides only reporting integration for JIRA

NOTE: this release introduces new database migrations!

NOTE: this release includes updated static files!

NOTE: this release introduces a new configuration setting called
``NITRATE_BASE_URL``. It defines the FQDN of your Nitrate instance!
This configuration is used to construct a URL linking back to test
cases and test runs when reporting bugs!


3.8.18.18 (May 1 2017, released on MrSenko.com)
-----------------------------------------------

- Rebased onto a2363f8
- Add default permissions to groups. PR #191 (Mr. Senko)
- Fix Issue #186: Errata field visible when ``ERRATA_URL_PREFIX`` is empty.
  PR #188 (Mr. Senko)
- Fix Issue #181: Failed to delete testplan or product. PR #182 (Mr. Senko)
- Add link to Administration guide in footer (Mr. Senko)
- Update MOTD displayed on login/registration form (Mr. Senko)
- Updated RPMs inside Docker image (Mr. Senko)
- Use bug trackers defined in the DB. PR #79 (Mr. Senko)

NOTE: this release introduces new database migrations!


3.8.18.17 (Apr 24 2017, released on MrSenko.com)
------------------------------------------------

- Rebased onto a1c47ec
- Updated removal of deprecated request.REQUEST from PR #156 (Mr. Senko)
- Updated tests from previous merge of PR #171 (Mr. Senko)
- Refactor SQL in testplans to ORM. PR #172 (Mr. Senko)
- Fix Issue #174 - Error when remove tag from a plan's cases (Mr. Senko)
- Refactor SQL in testcases to ORM. PR #177 (Mr. Senko)
- Improve tags search and fix hints while adding tags to selected test cases
  inside of a test plan. PR #178 (Mr. Senko)
- Update documentation about installation steps for RHEL6.
  PR #179 (Mr. Senko)
- Make it possible to build and run Nitrate as docker image.
  PR #180 (Mr. Senko)


3.8.18.15 (Apr 12 2017, released on MrSenko.com)
------------------------------------------------

- Rebased onto 8f45beb
- Remove tcms.core.migrations.0001_django_comments__object_pk


3.8.18.12 (Mar 22 2017, released on MrSenko.com)
------------------------------------------------

- Rebased onto 980b07b
- Add tests, SQL refactor and fixes for commit_unless_managed.
  PR #170, Issue #148 (Mr. Senko)
- Enable testing with MySQL and Postgres on Travis-CI. PR #171,
  Issue #169 (Mr. Senko)

3.8.18.10 (Mar 8 2017, released on MrSenko.com)
------------------------------------------------

- Rebased onto c696e62
- Don't use deprecated request.REQUEST. PR #156 (Mr. Senko)
- Update tests and fix Travis CI core dump. PR #168, Issue #161 (Mr. Senko)


3.8.18.09 (Feb 28 2017, released on MrSenko.com)
------------------------------------------------

- Rebased onto 7a6bc34
- Enable the test suite. Fix #113 (Chenxiong Qi)
- Refactor SQLs in xmlrpc (with tests). PR #159 (Mr. Senko)
- Enable Coveralls.io. PR #160 (Mr. Senko)


3.8.18.08.01 (Feb 21 2017, released on MrSenko.com)
---------------------------------------------------

- Don't install files under /etc/ to avoid SandboxViolation (Mr. Senko)


3.8.18.08 (Feb 21 2017, released on MrSenko.com)
------------------------------------------------

- Replace hard-coded SQL statements with ORM queries in reporting app.
  PR #146, fix #127 (Mr. Senko)


3.8.18.07 (Feb 14 2017, released on MrSenko.com)
------------------------------------------------

- Rebased onto 82625f1
- Add documentation about installation with Apache and virtualenv.
  PR #137 (Mr. Senko)
- Replace hard-coded SQL statements with ORM queries. PR #139 (Mr. Senko)
- Use version from module, not txt file. PR #145 (Mr. Senko)


3.8.18.05 (Jan 31 2017, released on MrSenko.com)
------------------------------------------------

- Rebased onto 698288e from upstream (Mr. Senko)
- Enable internal tests
- Drop support for Python 2.6 (Mr. Senko)
- Update help strings of clone case form and update docs. Fix #67 (Mr. Senko)
- Updated documentation with sections about hosting with
  Gunicorn, Docker and Google Cloud Engine (Mr. Senko)
- Remove raw SQL migrations and initial schema and data
- Add migration for django_comments
- Upgrade Django to 1.8.14
- Upgrade to django-tinymce 2.4.0 (Mr. Senko)


3.8.18.04 (Jan 24 2017, released on MrSenko.com)
------------------------------------------------

- Don't hard-code priorities in advanced search.
  PR #45, fixes RhBz #1139932 (Chenxiong Qi)
- Update to Django 1.8.11. PR #81 (Mr. Senko)
- Update django-tinymce to 2.4.0
- Update link to wadofstuff-django-serializers. PR #101, fixes #99 (Mr. Senko)
- Minor updates to documentation. PR #100 (Matthias Cavigelli)
- Require Celery<2 for compatibility reasons. PR #102 (Mr. Senko)
- Host static files in DEBUG mode for development. PR #103 (Mr. Senko)
- flake8 fixes. PR #104 (Mr. Senko)


3.8.18 (Aug 21 2016)
--------------------

- Relayout indentation in urls (Chenxiong Qi)
- Ignore .vagrant/ (Chenxiong Qi)
- Revert "move javascript to the bottom of page" (Chenxiong Qi)
- using DataTable to show test runs (Chenxiong Qi)
- move javascript to the bottom of page (Chenxiong Qi)
- i18n support (Chenxiong Qi)
- setup dev env with Vagrant (Chenxiong Qi)
- Better fix for traceback introduced by PR #86 (Mr. Senko)
- fix import conflict (Chenxiong Qi)
- Define variables in a way which works on non RPM based systems (Mr. Senko)
- Fix flake8 'E731 do not assign a lambda expression, use a def' (Mr. Senko)
- Fix flake8 E402 module level import not at top of file (Mr. Senko)
- Fix flake8 errors and remove a few unused methods (Mr. Senko)
- Rename non-existing fields in queries (Mr. Senko)
- Use STATIC_URL for a few images (Mr. Senko)
- update document for development environment setup (Chenxiong Qi)
- fix search_fields in management admin (Chenxiong Qi)
- fix flake8 errors (Chenxiong Qi)
- use Makefile to run flake8 (Chenxiong Qi)
- Prevent from scrolling page up when show and close tip of environment group
  (Chenxiong Qi)
- change file format from dos to unix (Chenxiong Qi)
- change TCMS to Nitrate in templates (Chenxiong Qi)
- support travis-ci (Chenxiong Qi)

3.8.17-1 (Feb 11 2015)
----------------------

- ignore empty string in white space character escape

3.8.16-1 (Feb 11 2015)
----------------------

- revert whitespace filter in run/testcaserun notes field

3.8.15-1 (Jan 23 2015)
----------------------

- add whitespace filter in plan/case/run text field

3.8.14-1 (Dec 22 2014)
----------------------

- Specify html.parser explicitly to parse HTML document

3.8.13-1 (Dec 18 2014)
----------------------

- Bug 1174111 [Test Plan]Test Plan doesn't recognize some scripts content when
  edit plan to upload html files.

3.8.12-1 (Dec 4 2014)
---------------------

- Refine documents

3.8.11-1 (Oct 15 2014)
----------------------

- TCMS-689 Write unittest for testcaserun, filters, tag, version
- TCMS-647 [Refine modulization] move app-specific code to each app-
- TCMS-541 move javascript code of template files into js files as
  many as possible
- TCMS-545 with the help of template engine(Handlebars.js),
  get rid of html snippets in js files
- TCMS-663 [RFE][test run] User must click 'show all' link to confirm whether
  there are comments to a caserun in run detail page.
- TCMS-666 [RFE][test run]When add issue_id to caserun,
  checked the option 'check to add Test Cases to BZ',
  system does not sync case_id to bugzilla.
- TCMS-688 Write unit test for xmlrpc.api.testplan and QuerySetBasedSerializer
- TCMS-704 Replace data grid with data table on search plan/run/cases page
- TCMS-714 [TestPlan] The plan name is invisible when the name contains
  java script contents.
- TCMS-702 Unit test for XMLRPC serializer method
- TCMS-659 Remove code that has already no effective in current TCMS feature
- TCMS-542 rewrite the js code for dom manipulation with jquery and jquery ui,
  remove prototype.js
- TCMS-549 rewrite the js code for event binding with jquery,
  remove contorls or effects based on prototype.js
- TCMS-184 Remove the outdate install section
- TCMS-716 [Add cases to run]There are js errors when expanding the case
  details in the assign case page.
- TCMS-717 [Search Cases]There is a js error in the console when clicking
  the Search Cases in the Testing tab.
- TCMS-748 Security check via Revok test

3.8.10-2 (Aug 27 2014)
----------------------

- Bug 1133483 - Unable to clone runs in TCMS
- Bug 1133912 - Script injection in notes field
- Bug 1134166 - [test plan] when user remove tag at reviewing case tag in
  test plan detail page, system returns 500 error

3.8.10-1 (Aug 18 2014)
----------------------

- Bug 1039495 - [test run][export to xml]If a case related many bugs in a run,
  when export the run to xml, the file only show the latest bug for this case.
- Bug 1129058 - [TestPlan|Add cases] The browser has no response and is in dead
  after selecting all the selected cases
- Bug 1130903 - [xmlrpc]User can not filter case via estimated_time when invoke
  TestCase.filter_count method.
- Bug 1130933 - [xmlrpc] User can not update estimated_time to 0s when invoke
  TestRun.update method.
- Bug 1130961 - [TestPlan|Components] Can't remove all the default components
  of one test plan at one time
- Bug 1130966 - [xmlrpc][document] The format of estimated_time for related
  methods should be consistent.
- Bug 1131885 - [XML-RPC] The Texts don't trim the spaces and record them
  as new versions when invoking the TestCase.store_text() and
  TestPlan.store_text()
- TCMS-284 [Performance] Production Apache ssl_access_log report some
  resources(such as css,js,pic etc) can not found(HTTP 404) (RHBZ:1035958)
- TCMS-371 [Performance Test][Reporting Custom] The First Slow Query on the
  Top Slow Queries found on prod evn (2014-06-05 to 2014-06-12)
- TCMS-425 TestRun & TestCase estimated_time modify
- TCMS-463 [Performance]Reporting Custom Section Optimize
- TCMS-464 [Performance]Reporting Testing Report Section Optimize
- TCMS-478 [xmlrpc]Invoke TestCase.calculate_total_estimated_time with a
  invalid input, system returns total_estimated_time 00:00:00 not 400 error.
  (RHBZ:1102459)
- TCMS-480 Enable system-wide cache mechanism to support caching
  (RHBZ:1027589)
- TCMS-481 [xmlrpc]The result for xmlrpc method
  TestCase.calculate_average_estimated_time is wrong. (RHBZ:1099312)
- TCMS-482 TestPlan.update does not support 'owner' update (RHBZ:1023679)
- TCMS-484 [test run] If a run has multiple Environments,
  clone this run, the new run only clone the latest Environment. (RHBZ:1112561)
- TCMS-485 [xmlrpc]when invoke TestCase.link_plan method,
  the 404 error message lack description. (RHBZ:1112967)
- TCMS-486 [RFE] Suggest improve "Testing Report" generating for large
  data query (RHBZ:870384)
- TCMS-487 [RFE]: Add test case to the plan by ID (number) (RHBZ:869952)
- TCMS-488 [XMLRPC] List all the methods related to "is_active"
  field which all needed to be fixed (RHBZ:1108009)
- TCMS-489 [test case]A bug belongs to Run A and Run B for the same case,
  remove this bug from Run A in case detail page, the bug for Run B is
  removed as well. (RHBZ:1094603)
- TCMS-492 replace TestRun.is_current with front-end control, and remove
  operation code against TestRun.is_current in view
- TCMS-493 fix that two requests are emit after change a case run's status
- TCMS-494 Build base infrastructure of unit test
- TCMS-495 Optimize operations on test_case_texts
- TCMS-496 rewrite the ajax style code snippets with jquery
- TCMS-498 [TestCaseRun | Add bug] The added jira bugs don't display in the
  case run but actually they are added in the xml file. (RHBZ:1119666)
- TCMS-499 [DB] Fix errors when syncdb
- TCMS-500 [Cache] Cache part sections of pages
- TCMS-512 [XML-RPC] TestCase.calculate_total_estimated_time() doesn't work
  (RHBZ:857831)
- TCMS-513 [Performance] TCMS Reporting respond slowly and cause MySQL server
  high CPU usage (RHBZ:1029267)
- TCMS-514 [XML-RPC] TestCase.calculate_average_estimated_time()
  doesn't work (RHBZ:857830)
- TCMS-515 [TestRun][RemoveCase]Remove case into creating test run,
  the test run's estimated time didn't sync with its cases totally
  estimate time (RHBZ:849066)
- TCMS-516 [xmlrpc] Can not add cases to the runs with calling the
  TestRun.add_cases() method (RHBZ:1119224)
- TCMS-551 [test run] After updating the Environment value in test run detail
  page, user can not remove the changed environment. (RHBZ:1124210)
- TCMS-552 [xmlrpc][document] The example for TestRun.get_test_case_runs method
  still support is_current parameter. (RHBZ:1126398)
- TCMS-553 [Testing report] Generate testing report By Case Priority,
  the Priority order for different builds were different. (RHBZ:1125828)
- TCMS-554 [testing report] If all plans belongs to a product have plan tag,
  system display 'untagged' in tag list in testing report by Plan's Tag
  (RHBZ:1125815)
- TCMS-555 [Testing report] Generate testing report by Plan's Tag Per Tag
  View, the caserun's count for idle status was wrong. (RHBZ:1125214)
- TCMS-556 [Testing report] Generate testing report
  By Plan's Tag Per Tag View, the total caserun's count statistic the
  duplicate caseruns. (RHBZ:1125821)
- TCMS-557 [TCMS-495 | Texts]Texts of test case and test plan don't support
  Chinese characters (RHBZ:1126790)
- TCMS-559 [testing report] the link on Paused status in testing report
  generated by Case-Run Tester was wrong. (RHBZ:1126353)
- TCMS-560 [testing report] Generate testing report by Case-Run Tester,
  the run's count was wrong. (RHBZ:1126359)
- TCMS-569 [testing report]Generate testing report By Plan's Tag Per Tag View,
  click link on caserun status to access caserun list,
  system returns 500 error. (RHBZ:1127621)
- TCMS-570 [TCMS-487| Add cases] Make sure the cases which had been added to
  the plan can't be searched by case id (RHBZ:1127522)
- TCMS-571 [test case]when create case without estimated_time,
  system can not save the case. (RHBZ:1126322)
- TCMS-572 [xmlrpc] Do not change the content of plan's text,
  invoke TestPlan.store_text twice, system will save the content twice with
  same checksum (RHBZ:1127194)
- TCMS-573 [test plan] If clone case with Create a Copy Settings,
  system will go to 500 error page. (RHBZ:1126304)
- TCMS-574 [xmlrpc] Invoke TestCase.get_text to get a nonexistent version,
  system returns 500 error. (RHBZ:1127198)
- TCMS-575 [clone test run] The estimated time format is different with input
  by manual (RHBZ:1126300)
- TCMS-585 Search cases lead memory leak in production server
- TCMS-619 [XMLRPC] default_product_version is missed in the response
  from TestPlan
- TCMS-96 [test plan][add child node]When add child note to plan with a
  nonexistent plan id, the submit btn in the warning form has no effect.
  (RHBZ:1038950)
- TCMS-98 [test run][add bug]Add reduplicative bug to case in the run page,
  the content of the warning is incorrect. (RHBZ:1039408)

3.8.9-3 (Aug 11 2014)
---------------------

- Hotfix XMLPRC backward-compatibility broken

3.8.9-2 (Aug 01 2014)
---------------------

- TCMS-538 Solve inconsistent data of product_version field in
  production database.

3.8.7-5 (May 22 2014)
---------------------

- TCMS-326 - [XMLRPC] Optimize TestRun.get_test_cases, which generates a slow
  query that would affect other SQL execution on test_case_runs table

3.8.7-3 (Apr 22 2014)
---------------------

- TCMS-264 - Temp workaround to avoid updates automatically bugzilla with TCMS
  test case ID.
- TCMS-240 - Convert column type, add composite index and add migrate sql for
  each release version.

3.8.7-2 (Apr 11 2014)
---------------------

- Bug 1083958 - [test run]In run detail page, using 'bugs-remove' link can
  remove the bug which does not belong to the current caserun.
- Bug 1083965 - [test run]In run detail page, using 'comment-add' link to add
  comment, system does not record author.

3.8.7-1 (Apr 03 2014)
----------------------

- Bug 1034100 - [Performance] opening plan/id/chooseruns page causes
  Python interpreter consumes very hight, around 100%, CPU usage
- TCMS-171 [BZ 866974] Provide TestPlan.{add,get,remove}_component
- TCMS-177 It takes over one min to mark one case to pass in test case run.
- TCMS-186 Too slow when create test run
- TCMS-187 [Performance] Loading test case when expand a test case pane in
  Cases and Reviewing Cases tabs in a test plan page is too slow.
- TCMS-188 [Performance] Loading test case when expand a test case pane in
  test run page is too slow
- TCMS-194 [Performance] Expand a plan to display case run list in Case Runs
  tab in a case page
- TCMS-195 [Performance] Expand a case run from case run list in Case Runs
  tab in a case page
- Using VERSION.txt file instead of writing version into tcms module directly

3.8.6-5 (Apr 01 2014)
----------------------

- Bug 1082150 - Backward-incompatible change in TestRun.get_test_case_runs()

v3.8.4 (Sep 17 2013)
--------------------
- Fixed bug # 1005797 - [RFE] Add a column with number of comments into
  Case Runs table
- Fixed bug # 921930 - Date format of attached log links is incorrect

v3.8.2 (Jul 25 2013)
--------------------
- Fixed bug # 988332 - Added one permission protected XMLRPC API to add group
  for a user.

v3.5 (Jul 11 2011)
------------------
- Fixed bug # 545082 - Test case sort order is shared across plans for
  cloned cases
- Fixed bug # 589633 - Not able to change author of plan
- Fixed bug # 646325 - [FEAT]cases link doesn't link to the special cases
- Fixed bug # 657160 - [TCMS3.2-2][RFE]Add tips after saving the basic
  information in the home page (Nitrate 3.2-2)
- Fixed bug # 658339 - [TCMS3.2-2]The "Upload" button is stealing the function
  of "Create test plan" button when create new test plan
- Fixed bug # 661613 - [Test Plan]Click "Upload" button without browse the
  attachment will report 404 error
- Fixed bug # 664700 - [FEAT] TCMS - NitrateXmlrpc: add method for new Product
  version creation
- Fixed bug # 665937 - cancel all the runs you want to clone will turn to
  the err page
- Fixed bug # 667584 - There is a Error when exporting Test Plan without
  choose a plan
- Fixed bug # 668323 - add build with non-English name succeeds but warning
  appears
- Fixed bug # 670996 - Sorting on test plan results page only sorts that page
  instead of all the results
- Fixed bug # 671457 - [RFE] removal confirmation dialogs should contain number
  of removed items
- Fixed bug # 672415 - Add a child node to a plan, input non-numbers, causing a
  dead loop
- Fixed bug # 673421 - Sometimes "file a bug on bugzilla" function doesn't work
- Fixed bug # 675096 - [RFE] chart showing success rate of test-plan-runs
- Fixed bug # 678052 - Tag link causes some nonsense text issues
- Fixed bug # 678203 - [test plan]The product version is not inconsistency in
  test plan
- Fixed bug # 678220 - [Basic Information]Can not save chinese name in
  basic information
- Fixed bug # 678465 - [Bookmarks]The box also be checked after delete
- Fixed bug # 678468 - [Bookmarks]There is no warning UI when delete bookmark
  without any choice
- Fixed bug # 678513 - [Search Plan]there is UnicodeEncodeError when searching
  plan via chinese tag
- Fixed bug # 678962 - [Component]Suggest pop-up the confirm UI when remove
  component
- Fixed bug # 678975 - [tag]The link of tag list cause the filter is not
  correctly
- Fixed bug # 679242 - [Test Case]Click "Upload" button without browse the
  attachment will report 404 error
- Fixed bug # 679243 - [Test Plan][RFE]Suggest to add the back button when
  add attachment in test plan
- Fixed bug # 679662 - [Clone Case]The "Autoproposed" can not be clone to
  the new case
- Fixed bug # 679663 - [Clone case]Can not select "Use the same Plan" after
  save the clone case without any plan
- Fixed bug # 679675 - [Test Run]There is a UnicodeEncodeError when add a
  chinese tag
- Fixed bug # 680379 - [Reporting]Click the plan number the result is not
  correct
- Fixed bug # 681328 - Filters are reset when cases are reordered
- Fixed bug # 682077 - [Quick search]quick search run,it goes to a error page.
- Fixed bug # 690057 - [test run]the test case detail will be auto updated
  without click update
- Fixed bug # 691413 - Reporting -> Custom page starts with
  'No builds found with search condition.'
- Fixed bug # 693281 - Web UI: drop down / list fields' values should be
  sorted alphabetically
- Fixed bug # 697252 - TCMS - nitrate xmlrpc: failed to attach bug info to
  TestCaseRun
- Fixed bug # 701591 - [Test case] Suggest "update component" should be
  "Add component" in test case and del the "remove" button
- Fixed bug # 701697 - Email notification has syntactical error (EN version) -
  new test run created
- Fixed bug # 703718 - [Usability] improve the layout the test case-run in run
- Fixed bug # 704101 - [Test Case] export test case without select any one
  will generate an error XML
- Fixed bug # 705983 - [report] product overview tab title can't be seen
  because the font is white.
- Fixed bug # 706062 - bugs shown in testcase detail
- Fixed bug # 707455 - [Test run]Can not re-order test cases in test run
- Fixed bug # 708883 - Click Bug Id could not link to bugzilla
- Fixed bug # 709764 - caserun link doesn't focus case in run
- Fixed bug # 710104 - Ordered list function of WYSIWYG: Numbers are not
  displayed.
- Fixed bug # 711005 - Return all relevant information in xml-rpc call
- Fixed bug # 711657 - The printable GUI can't show correctly
- Fixed bug # 712772 - [Test case]Export testcase without select any one
- Fixed bug # 712789 - Cannot open attachments
- Fixed bug # 713662 - [Extremely Urgent] Some test plans lost all|most|some
  test cases this afternoon.
- Fixed bug # 715209 - 100% Completion graphical progress bar does not look
  100%, it has still a gap to be filled.
- Fixed bug # 716499 - TestPlan.update() unable to update product version
- Fixed bug # 717521 - [test plan]spelling mistake on mouse over show
- Fixed bug # 717683 - XMLRPC: Unable to remove tag from plan
- Fixed bug # 717870 - problem to clone plan no. 3486
- Fixed bug # 719253 - [UI]UI problem of the input box for adding comment

v3.4.1 (Jun 10 2011)
--------------------
- Fixed bug # 590817 - Build reports include incorrect values
- Fixed bug # 642246 - Custom build report is incomplete
- Fixed bug # 653919 - [FEAT] filtering case-runs according to test-plan
- Fixed bug # 691412 - [TCMS] [Reporting] : no way to search according to
  case priority or plan tags
- Fixed bug # 691695 - [TCMS] [Reporting] : generate reports per user
- Fixed bug # 691696 - [TCMS] [Reporting] : generate reports for few build
  [multi selection]
- Fixed bug # 706839 - [Advanced search]When click link "Return to homepage",
  come out warning "Bad Request"
- Fixed bug # 707243 - bug links don't work

v3.4 (May 24 2011)
------------------
- Fixed bug #690423 - [xmlrpc] - xmlrpc loses connection to the server after
  a short timeout
- Fixed bug #593760 - xmlrpc doc doesn't match actual behavior: TestRun.update
- Fixed bug #593805 - xmlrpc Testcase.update fails when using certain arguments
- Fixed bug #662885 - Product version update failed for run 15325.
- Fixed bug #656098 - [FEAT] Relationship query
- Fixed bug #699311 - [New Plan]There aren't permissions to add
  "classification", "products", "versions"
- Fixed bug #705975 - [Printable copy]Can not printable copy one/more/all
  plan(s) in search list
- Fixed bug #705974 - [Export plan]Can not export one/more/all plan(s) in
  search list
- Fixed bug #697577 - pattern ID pointing to wrong place
- Fixed bug #682081 - [Test Case]Create a case with all fields,The UI is mess.
- Fixed bug #603622 - TestCase.add_component: adding already attached
  component results in traceback
- Fixed bug #637715 - TestCaseRun.update() should set tester to
  authenticated user
- Fixed bug #634295 - [FEAT]Bulk status change.
- Fixed bug #683844 - Update TinyMCE editor to recent version
- Fixed bug #683074 - One bug listed many times
- Fixed bug #669049 - [RFE] Editing a testrun - add a build.
- Fixed bug #644748 - Nitrate XML-RPC Service: failed to create new TestRun
  using the 'TestRun.create' verb.
- Fixed bug #587716 - FEAT - Need a new API call - to return a user object
  based on user ID's - such as tested_by_id
- Fixed bug #593091 - Programmatic access to TCMS via API requires user's
  Kerberos username/password
- Fixed bug #583136 - testplan.filter() returns plan objects that lack
  complete information
- Fixed bug #696047 - Default font size is too small in editor.
- Fixed bug #672124 - Default tester does not have permission to execute
  test run.
- Fixed bug #678184 - [Test Run]There are error info sorting test case in
  test run
- Fixed bug #680064 - [Test Run]The product version will be added to build list
  when Create New Test Run
- Fixed bug #690741 - [test run]Suggest can not remove the bug from other run
- Fixed bug #680032 - [Clone case][RFE]Add "cancel" button in
  mulitple clone page
- Fixed bug #680317 - [Test Run]The update function is invalid in test case run
- Fixed bug #680318 - [Create run]There is Warning about Data truncated when
  create run with more than 255 in summary
- Fixed bug #680380 - [Reporting]The warning UI is jumbled after select without
  choose product
- Fixed bug #679638 - [Test case]Print test case without choose any one is
  the same to choose all
- Fixed bug #698035 - [Sentmail]the reviewer received the TCMS mail rather
  than stage
- Fixed bug #593818 - Setting status=1 in TestRun.update should leave it
  in STOPPED state, but UI shows RUNNING
- Fixed bug #598882 - Changing status icon to 'start' or 'in progress'
  ("play" icon) jumps to next test case
- Fixed bug #663364 - [FEAT]Unable to search for multiple authors.
- Fixed bug #665052 - [FEAT] add test-case/test-run creation/completion date
  search criteria
- Fixed bug #671454 - [FEAT] search test-case by script
- Fixed bug #684804 - service error when accessing test-case from plan
  it is not a member of
- Fixed bug #615914 - [FEAT] searches with multiple products selected
- Fixed bug #670759 - [FEAT]Add a search item "Case Id"
- Fixed bug #680430 - [FEAT] search for test-cases from different products
- Fixed bug #653919 - [FEAT] filtering case-runs according to test-plan
- Fixed bug #542968 - [FEAT]Nitrate doesn't allow group operations on
  test case runs
- Fixed bug #564316 - [FEAT] tag searching - bugzilla-like categories or
  negative searching & regexps

v3.3-4 (Mar 3 2011)
-------------------
- Fixed bug 681156 - [Test Plan]Can not expand all the test case in test plan.
- Fixed Bug 679677 - [Test Run]The button should be "cancel" in Property page.
- Fixed Bug 672495 - Old test run shows updated case information but its
  text version is unchanged.

v3.3-3 (Feb 25 2011)
--------------------
- Fixed bug 680315 - [Reporting]Open a product will lead to the error page.
- Fixed bug 680321 - [Test Run]Click "View My Assigned Runs" will list all runs
- Fixed bug 627236 - s/2009/2010/ orequivalent of date in page footer
- Fixed bug 680322 - New: [spelling mistake]"Highligt" should be "Highlight"
- Fixed Bug 680059 - [Test Run]The total number of test case run is NULL
- remove "running date" add "run date"
- Fixed bug 676259 - [FEAT] Need to get a break out of manual vs auto in the
  tcms reporting section
- Fixed bug 678643 - TestPlan.get_text - multiple failures
- Fixed bug 674754 - [xmlrpc] TestRun.create() fails when list of tags provided
- Fixed bug 676590 - In run execute page, 'expand all' generates tons of http
  requests

v3.3-2 (Feb 15 2011)
--------------------
- Fixed bug 664025 - TCMS main check box to control test cases doesn't work
- Fixed bug 658372 - Cannot select "Product Version" when clone multiple
  test plans
- Fixed bug 667304 - Click "Build" label, it won't be sorted by build
- Fixed bug 654533 - [TCMS]Document Version in test plan on opera browser
- Fixed bug 672873 - xml export can't be parsed
- Fixed bug 664743 - [RFE] supply existing bugs when marking test-case-run as
  failed
- Fixed bug 672857 - Typo in error message when a test plan hasn't been
- Fixed bug 657474 [TCMS3.2-2]List the runs which have not environment
- Fixed bug 649293 - Make the case run "notes" field visible in the run
- Fixed bug 643324 - Provide a bit more space for the test run notes
- Fixed bug 653815 - Unable to re-order test cases in test run
- Fixed bug 658475 - The bug can not be deleted inside the run
- Fixed bug 672622 - product version gets set to "unused" when editing a plan

v3.3-1 (Jan 24 2011)
--------------------
- Fixed bug 661951 - Messed-up warning message pop up when clicking Add
  without entering Bug ID
- Fixed bug 665945 - run export button dosn't work
- Fixed bug 667293 - The first product is the default product.
- Fixed bug 665934 - choose no plan to "Printalbe Copy"
- Fixed Bug 654953 - [RFE] Report an expanded list of Test Cases by Tag
- Fixed bug 664467 - TCMS: cells overlapping when using long name for
  test case summary
- Fixed bug 662944 - Resort case run is broken in Firefox
- Fixed bug 642644 - update nitrate.py to work with the latest xmlrpclib
- Fixed bug 578717 - [REF] Provide filter in test run
- Fixed bug 653812 - Filtering test case runs
- Fixed bug 534063 - [RFE] Allow sorting / filtering test cases while executing
  the test run
- Fixed bug 660234 - Add links to IDLE, PASSED, WAIVED items in report
  table again
- Fixed bug 661579 - Incorrect bug counting method - Ugly code, Ugly bug
- Completed feature #662679 - Attachments get lost when cloning test case
- Completed feature #663520 QPID support for TCMS
- Completed global signal processor
- Fixed case run percent counter
- Improve the style of filtering test case runs

v3.2-4 (Dec 1 2010)
-------------------
- Fixed #658160 - Changing case status does not work reliably
- Fixed UI Bug #658495 - Some case run comments not displayed
- Re-enabled assignee update notification.

v3.2-3 (Nov 30 2010)
--------------------
- Fixed UI Bug #654944 - [TCMS][RFE]Email content:Assign cases to …
- Fixed UI Bug #656215 - Select all checkbox in search run page broken.
- Fixed #646912 - editing TC, leaving all automated/manual/autoproposed …
- Remove the JSCal2 DateTime? widget(no longer in use).
- Added grappelli skin for tinyMCE
- Fixed UI Bug #657452 - [TCMS3.2-2]put mouse on the status buttons and no
  tips …
- Fixed #658385 - TCMS is spamming with "Assignee of run X has ben …
- Fixed #658181 - TCMS xmlrpc: 403 FORBIDDEN

v3.2-2 (Nov 23 2010)
--------------------
- Fixed own username/email in user profile display without register support
- Completed UI FEAT - Add case default tester in search plan
- Fixed username regex like Django restrictive
- Swap the first/last name in profile
- Fixed the run information style
- Fixed #652474 - Unable to update "Basic information" fields.
- Fixed UI Bug - 652478 - Inconsistent size, font weight in Test Plan Cases tab
- Fixed #654211 - [TCMS]search run product is not same with run detai
- Fixed #654967 - [TCMS]Fail to add Properties to environment group and show …
- Fixed #654955 - [TCMS]fail:Search Test Run by Manager
- Fixed #654949 - [TCMS]Fail:Remove Case from Test Run
- Fixed UI Bug #654213 - New: [TCMS][REF]Remove "Test" in TESTING--->Search …
- Fixed UI Bug #654505 - [TCMS][REF]Where is Description of bookmark.
- Fixed UI Bug #654529 - [TCMS]Unify tips about Upload file format
- Fixed #654922 - [TCMS]Fail:Remove test cases tag
- Fixed #589633 - Not able to change author of plan
- Fixed UI Bug #654553 - [TCMS]Default Component
- Fixed UI Bug #627074 - Planning: Default components "update" removes …
- Fixed #656174 - Can't record Case or Case-Run Log

v3.2-1 (Nov 9 2010)
-------------------
- Fixed UI Bug #635329 - [TCMS]a small spelling mistake
- Fixed #635369 - Add a test case with tags will fail via tcms xmlrpc
- Fixed #635931 - [TCMS]The blank row in Status' drop-down box of
  Search test Runs
- Fixed UI Bug #637471 - [TCMS][REF]The style in the home page
- Completed Feature #637271 - Provide an XMLRPC function for adding a
  test case run comment
- Makes Django 1.2 compatible
- Add csrf to templates/admin pages for Django 1.2
- Fixed #638639 Test run report "Finished at" field shows "Notes" content
- Fixed UI Bug #638019 -[REF]Test Runs in the home page
- Bug UI Bug #641252 - [TCMS][REF]"Testing Cases" to "Cases" in REPORTING
- Refined the js, split the case to confirmed cases and reviewing cases
- Fixed #637474 - [TCMS][REF]The sort of "Plan Type" data and the sort of
  "Environment Group" data in Search Plan page.
- Fixed new admin URL
- Fixed #634218 - Text box "Comment" is erased when timestamp expires
- Fixed #634218 - clean_timestampe-->clean_timestamp
- Fixed #638808 - The calendar icon broken after upgrade to django 1.2.3
- Completed feature #634157 - Preselect product when adding new build
- Fixed #637276 - TestCaseRun.attach_bug broken
- Fixed #637715 - TestCaseRun.update() should set tester to authenticated user
- Fixed UI Bug #643349 - Wrong product displayed on the test run execute page
- Fixed #638526 - [TCMS]Refresh Page fail after "Disable Plan"
- Fixed UI Bug #643324 - Provide a bit more space for the test run notes
- Completed refine the test case review workflow
- Fixed #644252 - error when modify the product name
- Fixed UI Bug #644356 - Allow to sort test case runs
- Fixed UI Bug #644354 - Displaying test case run details breaks layout
- Fixed #644748 - Nitrate XML-RPC Service: failed to create new TestRun
  using the 'TestRun.create' verb
- Completed basic info editing/viewing in profile
- Add the title/nav/footer to 404 & 500 error page
- Add NEED_UPDATE status to test case status
- Fixed UI Bug #629122 - [REF] Display test case notes when expanding a
  test case
- Fixed UI Bug #641790 - [TCMS] No warning after inputting "1.1" in the sort of
  case
- Fixed UI Bug #643303 - [RFE] test-run report - show bugs near corresponding
  test-cases
- Initial completed bookmark feature
- Completed reviewer for case and the mail notification when update reviewer
- Fixed #640756 - can't remove bugs from a test-case
- Fixed #646324 - service error display when cancel tag edit
- Fixed #638476 - Duplicated environment group name will cause error
- Fixed #601756 - Editing a test case erases "component" field
- Fixed #519029 - All URLs should be linkified
- Fixed UI Bug #648760 - The spelling mistake happened in Estimated time
- Arranged toolbar in the way mentioned
- Merged the index page to profile
- Fixed default url redirect after login
- Initial completed the clone mulitple run from plan function
- Refine Home page
- Initial refined the mass status/priority operation function
- Fixed add bookmark without content_type issue
- Fixed UI Bug #646340 - no warning is displayed when test plan is not selected
- Changed commit style, added order to comment
- Fixed #636813 - No direct link to comment of run
- Fixed #646399 - In case permission are not granted,
  you are asked for login credentials that are never accepted.
- Fixed redirect to review cases after case creation
- Refined the delete comment feature
- Fixed log display in details page
- Fixed auto case expanding in run page
- Fixed #637870 - The sum of the percentage of the test status categories on
  the overall report for a given build do not sum to 100%
- Fixed toolbar style on Chrome and safari
- Fixed update assignee feature
- Completed password change feature
- Removed the execute run link
- Completed registration feature
- Completed password reset feature
- Refined the update case run text and re-order case run feature
- Completed paginatation for case/run/plan list
- Fixed #645631 - need item to type Test Plan id directly when clone test case
- Fixed #648325 - When clone multiple, check 'update manager', it has an error
- Linked the user linke to profile

v3.1.1-3 (Sep 17 2010)
----------------------
- Fixed global plan search issue.

v3.1.1-2 (Sep 15 2010)
----------------------
- Optimized the performance for pagination
- Fixed #630604 - disabled test cases included in /plan/<XYZ>/printable/
- Fixed #564258 - [REF] Ability to export/print specified cases
- Fixed UI Bug #626276 - [TCMS]reporting:link to failed test cases not working
- Fixed UI Bug #633618 - Tree view - text changes
- Fixed #633681 - JS error info in "search plan" and "search case" page …
- Fixed #634045 - Tag auto-completion failed to work.

v3.1.1-1 (Sep 8 2010)
---------------------
- improve the run report
- Fixed UI Bug #626720 - see all link does not work
- Fixed UI Bug #625646 - Text changes for reporting UI
- Fixed UI Bug #626237 - Text change for Test Plan UI
- Fixed UI Bug #626719 - When expand case, the width is wrong by default
- Fixed custom reporting search condition
- Fixed UI Bug #624861 - Display related bugs in customization report
- Fixed UI Bug #626276 - Reporting:link to failed test cases not working
- Fixed UI Bug #625789 - Add Plan input field do not control its input and …
- Added highcharts for future reporting
- Add pagination feature for TCMS test plans, test cases and test runs using …
- Fixed #628421 - Cannot remove test run tags.
- Fixed UI Bug #625797 - test case run history should display test run
  summaries
- Fixed #626638 - Product version is not copied from the original when …
- Fixed #627235 - Adding a build requires reloading page.
- Fixed UI Bug #629977 - test-run report does not contain test-run name
- Completed feature #542660 - TCMS: [FEAT] - allow to add sub test suite for
  test plan
- Refined add plan to case feature
- Completed add multiple plan to a case feature
- Fixed UI Bug #629508 - [TCMS]Create button and Test Plan box are overlapping
- Fixed UI Bug #629508 - [TCMS]Create button and Test Plan box are overlapping
- Fixed #627236 - s/2009/2010/ in footer
- Fixed #629617 - remove white spaces from beginnig and at the end of …
- Added parent modify feature to XML-RPC

v3.1.0-2 (Aug 12 2010)
----------------------
- Enhanced the reporting feature.

v3.1.0-1 (Aug 12 2010)
----------------------
- Fixed #612803 - add an export feature for test case runs, can export …
- Fixed #609777 - Tag autocomplete for "remove tag" shows all possible …
- Completed Feature #578887 - Clone all test runs for a particular build of …
- Fixed #618710 - Env value for test run permission checking
- Completed feature #599313 - [REF] Mass edit test case components
- Fixed #619247 - Cannot update test case status
- Fixed #591823 - Sort by "completed" can work correctly.
- Fixed #618183 and #619403 - Notification of case editing issue
- Fixed #599448 - add upload feature while editing a plan.
- Fixed #621777 - TCMS gives error message on screen after edit->save …
- Fixed #598409 - "RFE: add plan creation date search criteria", add a …
- Completed new report with customization

v3.0.4-3 (Aug 2 2010)
---------------------
- Fixed #612797 - The Property in Environment can not be deleted
- Fixed #616463 - Remove property doesn't work in TCMS

v3.0.4-2 (Jul 30 2010)
----------------------
- Fixed #619247 - Cannot update test case status

v3.0.4-1 (Jul 21 2010)
----------------------
- First open sourced version.
- Added all of docs lacked for installation/upgrading/usage.
- Fixed #604206 - TestCase.link_plan() does not report errors
- Completed feature #609842 - [FEAT] provide buglist link in addition to ...
- Fixed #611354 - [Text] Updates to automation options.
- Fixed UI Bug #609760 - Add Tag text "Ok, I see" needs updating.
- Fixed UI Bug #606730 - favicon.ico should use transparency
- Fixed #612797 - Test run env value permission check issue
- Fixed #612022 - Change Automation status window appears when no test …
- Fixed #609776 - Tag autocomplete is case sensitive.
- Fixed #612881 - The filter for 'Automated' 'Manual' 'Autoproposed' is …
- Fixed #613480 - No way is provided to go back to the plan after cloning a …
- Fixed UI Bug #610127 - show/highlight test-case-runs assigned to me when
  executing …
- Fixed UI Bug #612880 - Need total number for filter out result
- Completed feature #607844 - (RFE) Flag tests which require the IEEE Test …
- Completed Feature #587143 - [FEAT] Have a default component when creating …
- Move the compoent of the case to be a tab
- Use the updateObject() function to reimplemented multiple operations.

v3.0.3-2.svn2859 (Jun 28 2010)
------------------------------
- Fixed bug #604860. Modify ComponentAdmin?'s search_fields from
  (('name',)) …
- Update the plan list & case list & run list
- Update the case run list
- Change from_config()'s return value from Nitrate to NitrateXmlrpc?
- Fixed #606751 - grammar error on dashboard
- Fixed #605918 - Submitting larger comments fails
- Completed edit environment in run page
- Use updateObject() function to modify the sortkey for caserun
- Fixed create case failed issue
- Completed feature #604860 - further improvement Add 'pk' for each item
  under …
- Fixed #608545 - [REF] Simplify the estimation time choosing
- Fixed TestCase?.link_plan function returns
- Fixed #603752 - Cannot reassign tests in this test run: …
- Fixed #603622 - TestCase?.add_component: adding already attached component …
- Optimized front page display

v3.0.3-1.svn2841 (Jun 12 2010)
------------------------------
- Fixed UI Bug #600198 - TCMS][3.0.2-1] - Buttons not Visible in Add New Test …
- Completed feature #588974 - Make edit work flow more efficient
- Fixed remove case function in plan
- Fixed #602183 - TestCase.create requires plan id
- Fixed #602292 - TestCase.create() does not save "estimated_time"
- Fixed #601836 - Unable to change test case category using XML-RPC
- Completed Feature #587143 - [FEAT] Have a default component when creating …
- Fixed UI Bug 601693 - Test case field "arguments" not available in the web …
- Completed Feature #597094 - Edit environment of existing test run is not …
- Completed Feature #598882 - Changing status icon to 'start' or 'in …
- Initial completed feature #595372 - Environment available through xml-rpc
- Fixed #603127 - Quick test case search broken
- Fixed UI Bug #591783 - The assigned run should be in my run page
- Fixed edit env property/value name to exist name caused 500 error

v3.0.2-2.svn2819 (Jun 8 2010)
-----------------------------
- Fixed #598935 - strip whitespace when adding bug numbers
- Fixed #598909 - Bugs filed from tcms contains HTML
- Fixed UI Bug #599465 - Filtering test plans based on the author broken
- Fixed #593091 - Programmatic access to TCMS via API requires user's
  Kerberos username/password
- Fixed tags lacked after search issue.
- Optimized batch automated operation form
- Fixed some UI issues.

v3.0.2-1.svn2805 (Jun 3 2010)
-----------------------------
- Use livepiple to replace scriptaculous and clean up the js codes.
- Added initial data for syncdb.
- Added unit test script.
- Merged testplans.views.cases and testcases.views.all
- Ability to mark test case as 'Manual', 'Automated' and 'Autopropsed'
- Fixed TestRun.update() XML-RPC docs.
- Fixed #593805 - xmlrpc Testcase.update fails when using certain arguments.
- Fixed #593664 - Misinterpreted e-mail about test run.
- Fixed UI Bug #591819 - Icons and links made mistakes in test review.
- Fixed UI BUg #594623 - Test run CC can not be added.
- Completed FEAT Bug #583118 - RFE: Attachments for test-runs.
- Fixed #594432 - tags are not imported from xml.
- Completed FEAT #586085 - Don't select ALL test case after changing status
- Completed FEAT UI Bug #539077 - Provide an overall status on main
  test run page
- Completed FEAT BUg #574172 - If you sort a column in a plan,
  the filter options …
- Fixed Bug #567495 - Sort by category for 898 test cases results in 'Request …
- Completed FEAT #597705 - TCMS: Unknown user: when user name have space
  before or …
- Fixed Bug #597132 - Cannot add environment properties to test run
- Completed FEAT #578731 - Ability to view/manage all tags of case/plan.
- Fixed Bug #595680 - TCMS: cannot disable a test plan
- Fixed Bug #594566 - Get test case category by product is broken

v3.0.1-3.svn2748 (May 19 2010)
------------------------------
- Fixed #592212 - Search for test cases covering multiple bugs
- Fixed #543985 - sort testplans on "clone test case" page alphabetically
- Fixed #561234 - [feature request]should filter out “the space” key in all …
- Fixed UI Bug #577124 - [TCMS] - "Show comments" without number --remove …
- Fixed UI Bug 592974 - Adding a test case to a plan using plan id does not …
- Fixed report 500 service error
- Fixed #592973 - Add cases from other plans fails with a service error
- Fixed get_components XML-RPC typo mistake and added docs to new filter …

v3.0.1-2.svn2736 (May 13 2010)
------------------------------
- Completed signal handler for mailing by a standalone threading
- Fixed test plan link for #591819
- Fixed 519029
- Optimized the menu style

v3.0.1-1.svn2728 (May 11 2010)
------------------------------
- Refined whole UI.
- Optimized query count for performance.
- Add examples to XML-RPC docs.
- Completed following methods for XML-RPC: Product.filter(),
- Product.filter_categories(), Product.filter_components(),
  Product.filter_versions(),
- Product.get_component(), Product.get_tag(), Product.get_versions(),
- Product.lookup_id_by_name(), TestCase.calculate_average_estimated_time(),
- TestCase.calculate_total_estimated_time(), User.filter(), User.get(),
- User.update().
- Fixed UI bugs: #590647, #583908, #570351, #588970, #588565, #578828, #562110,
- #582958, #542664.
- Fixed app bugs: #582517, #582910, #584838, #586684, #584342, #578828
- #577820, #583917, #562110, #580494, #570351, #589124, #577130, #561406,
  #586085, #588595, #560791, #584459.

v3.0-1b2.svn2665 (Apr 16 2010)
------------------------------
- Fixed #582517 - remove tag doesn't work
- Fixed #582910 - Automatic Display of Next Test Case Not working properly.
- Fixed #574663
- Completed Ability to edit environment for existed test run
- Completed change case run assignee feature
- Completed get form ajax responder
- Optimized get info responder

v3.0-1b1.svn2650 (Apr 14 2010)
------------------------------
- Initial completed most new features, extend database schema
- Initial completed bookmark(watch list) feature(Models added)
- Initial completed modify run environment value feature(Backend code)
- Extend the schema for outside bug track system(Backend code)
- Improve run mail feature
- Optimized XML-RPC and the docs
- Fixed 'Save and add another' crash when create new case
- Fixed Assign case to run and create new run without default tester.
- Fixed Build.create() bug
- Fixed TestRun.get_test_case_runs() bug

v2.3-5.svn2599 (Apr 1 2010)
---------------------------
- Fixed add tag to run cause to crash issue.

v2.3-4.svn2594 (Mar 29 2010)
----------------------------
- Completed create/update functions for XML-RPC.
- Fixed web browser compatible issues.
- Improve review case progress.

v2.3-3.svn2577 (Mar 23 2010)
----------------------------
- Fixed Webkit based browser compatible issues
- Fixed TinyMCE in Webkit based browser compatible issues
- Fixed UI Bug: #570351
- Fixed UI Bug: #553308

v2.3-2.svn2568 (Mar 22 2010)
----------------------------
- Fixed search case without product issue(r2567)
- Fixed create run foot UI issue(r2566)
- Fixed update component in search case issue(r2565)

v2.3-1.svn2564 (Mar 18 2010)
----------------------------
- Complete most of XML-RPC functions.
- Complete batch operation for case including setting priority, add/remove tag.
- Fixed most of bugs.

v2.2-4.svn2504 (Mar 17 2010)
-----------------------------
- Fixed version in web ui incorrect.

v2.2-3.svn2504 (Mar 12 2010)
----------------------------
- HOT BUG FIXING - #572487

v2.2-2.svn2504 (Mar 4 2010)
---------------------------
- Fixed UI bug: Execute link exceed the width issue
- Fixed UI bug: CC for run page display issue

v2.2-1.svn2500 (Mar 1 2010)
---------------------------
- Add a new serializer for XMLRPC serialization
- Fixed KerbTransport authorization issue
- Change deployment method to WSGI
- A lot of bugs fixing for application.
- Fixed a lot of UI bugs

v2.1-4.svn2461 (Feb 11 2010)
----------------------------
- Fixed application bug #561620
- Fixed web UI bug #529807
- Fixed web UI bug #561610
- Fixed web UI bug #552923
- Fixed web UI bug #561252
- Fixed web UI bug #553308
- Fixed web UI bug #558955
- Fixed web UI bug #560091
- Fixed web UI bug #560055

v2.1-3.svn2449 (Feb 2 2010)
---------------------------
- Remove product version from case search page.
- Optimize search case form.

v2.1-2.svn2446 (Feb 2 2010)
---------------------------
- Fixed the case display with the bug added directly in case page in run issue.
- Fixed edit case component selector issue.
- Case product link to category now, disconnect from plan.

v2.1-1.svn2443 (Feb 1 2010)
---------------------------
- Rewrite get case details to ajax code, for optimize performance
- Add tag support for test run
- Add bug to case directly now supported.

v2.0-3.svn2403 (Jan 18 2010)
----------------------------
- Fixed hot issue #556382

v2.0-2.svn2402 (Jan 18 2010)
----------------------------
- Fixed auto blind down issue
- Fixed #555702
- Fixed #555703
- Fixed #555707 and #554676
- Completed add tag to case/plan when create backend function

v2.0-1.svn2394 (Jan 15 2010)
----------------------------
- Fixed most of bugs
- The component will add to new product specific in clone function
- Use Cache backend to handle session
- More optimization

v2.0-1RC.svn2368 (Jan 11 2010)
------------------------------
- Fixed a lot of bugs
- Optimize new comment system
- Completed new log system
- Add new case fiter to plan
- Improve new review workflow
- Update setup.py

v2.0-1beta.svn2318 (Dec 29 2009)
--------------------------------
- First public beta release of 2.0
- Rewrite most components
- Add estimated time into run
- Add test case review workflow
- Add XML-RPC interface
- Use a lot Ajax to instead of render whole page
- Redesign the interface

v1.3-3.svn2261 (Dec 18 2009)
----------------------------
- Add case run changelog show in run details page feature

v1.3-2.svn2229 (Dec 8 2009)
---------------------------
- Fixed #544951
- Fixed #544229
- Fixed #543985
- Fixed #544951
- Fixed reporing when plan count is null issue
- Update overview report of product statistics SQL

v1.3-1.svn2213 (Dec 4 2009)
---------------------------
- Fixed #541823
- Fixed #541829
- Optimize delete case/run ACL policy.
- Initial completed Reporting feature.
- Initial XML-RPC interface

v1.2-3.svn2167 (Nov 25 2009)
----------------------------
- Made a mistake in checkout the source, so rebuild it.

v1.2-2.svn2167 (Nov 25 2009)
----------------------------
- [2152] Fixed bug #530478 - Case run case_text_version is 0 cause to file bug
  crash
- [2154] Fixed bug #538747
- [2156] Use QuerySet update function to batch modify the database
- [2158] Fixed bug #540794 - [FEAT]It should stay in the same tab/page after
  refreshing
- [2162] Restore search detect in plan all page
- [2163] Fixed bug #538849 - Test case execute comment garbled
- [2165] Fixed bug #540371 - Where are Cloned Tests

v1.2-1.svn2143 (Nov 20 2009)
----------------------------
- Fixed UI bug #530010 - clean float dialog
- Fixed UI bug #531942 - Correct strings in system
- Fixed UI bug #536996
- Fixed UI bug #533866 - sort case in test case searching
- Optimize a lot of UI and frontend permission control
- Fixed bug #536982 - Now the run must be required with a case
- Remove manage case page
- Enhanced sort case feature with drag and drop in plan and run
- Completed change multiple case status at one time
- Completed change run status feature
- Completed clone multiple plan feature
- Completed upload plan document with ODT format
- Fixed bug #533869 - "Save and add another" case button results in a traceback
- Completed case attachment feature

v1.1-1.svn2097 (Nov 9 2009)
---------------------------
- Release 1.1 version TCMS
- Completed clone case/run feature
- Refined the UI structure
- Add XML-RPC interface for ATP

v1.0-9.svn2046 (Nov 9 2009)
---------------------------
- Add mod_auth_kerb.patch for authorize with apache kerberos module.

v1.0-7.svn2046.RC (Oct 22 2009)
-------------------------------
- Improve templates

v1.0-6.svn2046.RC (Oct 22 2009)
-------------------------------
- Imporove test plan clone feature
- Fixed failed case run count in run details page
- Add RELEASENOTES

v1.0-5.svn2042.RC (Oct 21 2009)
-------------------------------
- Realign the version to 1.0
- Fixed most of bugs

v2.0-4.svn2006.RC (Oct 16 2009)
-------------------------------
- Fixed other unimportant bugs, release RC.

v2.0-3.svn1971 (Oct 14 2009)
----------------------------
- Fixed most of bugs and get ready to GA.
- KNOWN ISSUE: Search case to add to plan just complete the page design,
  is waiting for logic function.

v2.0-2.svn1938 (Sep 30 2009)
----------------------------
- Rewrite assign case page
- Rewrite attachment implementation
- Search with environment is available
- Fixed app bugs:
- Fixed #524578 - The Product version will display after finish searching plans
- Fixed #524568 - Cannot reset the status of test cases when the status is
  "Passed" or "Failed"
- Fixed #524534 - Can't add a new test case
- UI Bugs:
- Fixed #524530 - Please adjust the Next button in create new plan page
- Fixed #525044 - The buttons are not aligned and missing some checkboxes
  when searching cases
- Fixed #524568 - Cannot reset the status of test cases when the status is
  "Passed" or "Failed"
- Fixed #524140 - Cannot create test plan when the uploaded plan document's
  type is HTML
- Fixed #525614 - The label that counts the number should at the same place on
  every ADMIN's sub-tab
- Fixed #524777 - [FEAT]It should have breadcrumbs on Admin tab have added
  breadcrumb to admin page
- Fixed #525630 - The calendar and clock icon should be kept on the same line
  with date and time
- Fixed #525830 - The same buttons aligned in different tabs should keep
  consistent
- Fixed #525606 - "Is active" should be kept on the same line with its
  check-box

v2.0-2.svn1898 (Sep 23 2009)
----------------------------
- Feature:
- Completed environment element modfiy/delete feature in admin
- Fixed #525039 - [FEAT]It should let users add notes and set status of
  test cases even when the status of the test run is "Finished"
- UI Bugs:
- Fixed #521327 - Test Plan Document translation not quite right
- Fixed #524230 - can't change the "automated" field of a test case
- Fixed #524536 - Suggest to adjust the add new test case page width and
  the button "Add case"
- Fixed #524530 - Please adjust the Next button in create new plan page
- Fixed #518652 - can't remove test case from a plan
- Fixed #524774 - [FEAT]It should have a title on each of the add
  "Admin=>Management" webpage
- Fixed #525044 - The buttons are not aligned and missing some checkboxes when
  searching cases
- Fixed #524778 - [Admin]The add icons should be after the fields

v2.0-1.svn1863 (Sep 15 2009)
----------------------------
- Remove case from plan
- Sort case in plan
- Fixed edit case issue

v2.0-1.svn1833 (Sep 1 2009)
---------------------------
- Fixed a lot of bug.
- Redesign the interface.

v2.0-1.svn1799 (Jul 22 2009)
----------------------------
- Rewrite most of components
- Add tables from Django
- dump version to 2.0 (trunk development version)

v0.16-6.svn1547 (Mar 19 2009)
-----------------------------
- require kerberos authentication
- svn r1547

v0.16-5.svn1525 (Mar 17 2009)
-----------------------------
- mark tcms/product_settings.py as being a config file
- add dependency on mod_ssl

v0.16-4.svn1525 (Mar 17 2009)
-----------------------------
- substitute RPM metadata into the page footer so that it always shows
  the exact revision of the code
- bump to svn revision 1525

v0.16-3.svn1487 (Mar 12 2009)
-----------------------------
- drop the dist tag

v0.16-2.svn1487 (Mar 12 2009)
-----------------------------
- add build-requires on Django to try to get pylint to work
  (otherwise: tcms/urls.py:11: [E0602] Undefined variable 'patterns')

v0.16-1.svn1487 (Mar 12 2009)
-----------------------------
- 0.16
- add build-requires on python-setuptools

v0.13-4 (Feb 24 2009)
---------------------
- fix regexp for pylint errors

v0.13-3 (Feb 24 2009)
---------------------
- add code to invoke pylint.  Stop building the rpm if pylint finds a problem.

v0.13-2.svn1309 (Feb 18 2009)
-----------------------------
- add mod_python and python-memcached dependencies
- move static content to below datadir
- add apache config to correct location

v0.13-1.svn1294 (Feb 12 2009)
-----------------------------
- initial packaging


.. _open source bounty program: https://kiwitcms.org/blog/tags/bounty-program/
