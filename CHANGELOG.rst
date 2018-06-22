Change Log
==========


Kiwi TCMS 4.2 (23 June 2018)
----------------------------

**IMPORTANT:** this release introduces new database migrations, security updates
and GDPR related changes! It is also the first release after a great deal of
travelling for various conferences.

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
- Add pylint plugin to check for class attributes enclosed with double underscores.
  These are dunders and are reserved for Python!


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
- [docs] Remove information about importing test cases via XML. This functionality
  was removed in version 3.49



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
  item in the Cases tab. Also remove the export buttons from search and advanced
  search result templates. If you'd like to export the cases from a given
  plan you have to open it in a new browser window and use the menu
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
- Rename ``TestCase.notification_get_cc_list`` to ``TestCase.get_notification_cc``
  and update signature
- Rename ``TestCase.notification_remove_cc`` to ``TestCase.remove_notification_cc``
  and update signature
- Update signature for ``TestCase.remove_component``
- Update signature for ``TestCase.remove_tag``
- Remove ``TestCase.store_text``, use ``TestCase.update`` with
  ``setup``, ``breakdown``, ``action`` and ``effect`` attributes in the parameter dict
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
- Rename ``TestRun.remove_cases`` to ``TestRun.remove_case`` and update signature
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
  need to have ``attachments.add_attachment`` and ``atachments.delete_attachment``
  permissions.

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
  As part of this change the XML-RPC endpoint has been changed to ``/xml-rpc/``.
  There's also a new JSON-RPC endpoint at ``/json-rpc/``!
- ``Auth.login`` method now accepts positional parameters ``username, password``
  instead of dict
- ``TestCaseRun.get`` method now accepts a query dict as parameter
- ``TestCaseRun.get_bugs`` method now accepts a query dict as parameter

- Remove ``Build.lookup_id_by_name``, ``Build.lookup_name_by_id`` RPC methods
- Remove ``Product.lookup_name_by_id``, ``Product.lookup_id_by_name`` RPC methods
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
- Remove ``TestCaseRun.get_completion_time``, ``TestCaseRun.get_completion_time_s``
  RPC methods. Instead calculate them on the client side
- Rename ``TestCaseRun.check_case_run_status`` to ``TestCaseRun.get_case_run_status_by_name``
- ``TestCaseRun.detach_log`` will not raise exceptions when deleting logs from
  non-existing TestCaseRun objects.
- Remove ``User.get_me``, instead use ``User.get`` without parameters
- Remove ``Version.`` and ``Testopia.`` RPC modules
- Update documentation for RPC methods in ``Auth``, ``Build`` and ``Env`` namespaces.
  Unformatted documentation is also available for the rest of the RPC methods

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
- Show status name rather than status id in TestCaseRun change log. (Chenxiong Qi)
- [api] Adds a Python API client with changes that make it possible to
  execute on both Python 2 and Python 3. For now take a look at
  ``tcms_api/script_examples/`` for examples how to use it.
  NOTE: API client has been initially developed as the *python-nitrate*
  project by Petr Splichal and other contributors.
- [api] Remove experimental support for Teiid. (Mr. Senko)
- [api] Cache level defaults to ``CACHE_NONE`` if not set. (Mr. Senko)
- [api] Remove persistent cache, in-memory caching is still available. (Mr. Senko)
- [api] Remove multicall support. (Mr. Senko)


IMPORTANT: this release introduces new database migrations!


3.44 (Oct 31 2017)
------------------

- Use correct django_comment permission name. Allows non-admin users to enter
  comments. Fixes `Issue #74 <https://github.com/MrSenko/Kiwi/issues/74>`_. (Mr. Senko)
- Fix 500 ISE when viewing other user profiles (Mr. Senko)
- Add a more visible link to account registration in the MOTD section
  of the login page (Mr. Senko)
- Use correct permission names when editting Test Plan Environment Group field.
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

    MariaDB defaults are to use ``latin1`` as the default character set and collation.
    This will lead to 500 internal server errors when trying to save data which
    does not use ASCII characters. This is a limitation with the underlying CentOS/MariaDB
    docker image and a `solution <https://github.com/CentOS/CentOS-Dockerfiles/pull/146>`_
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
- ``USER_GUIDE_URL`` setting has been removed. You can specify this configuration
  directly in ``FOOTER_LINKS`` (Mr. Senko)
- Added missing templates and views for password reset functionality (Mr. Senko)
- Makefile updates and flake8 fixes (Mr. Senko)


3.38 (Sep 20 2017, released on MrSenko.com)
-------------------------------------------

- Bug fix: Test Case EDIT and CLONE buttons are now working again (Mr. Senko)
- More tests and better handling of input parameters when loading builds
  (Mr. Senko)
- Load more of the required JavaScript and CSS files for admin forms (Mr. Senko)


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
  causing DB connections to be closed after view functions have returned (Mr. Senko)
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
- Removed dependency on qpid-python and QPID integration which has been disabled
  for a long time and most likely not working. This removes the ``ENABLE_QPID``
  setting as well. Fixes

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
- Update documentation about installation steps for RHEL6. PR #179 (Mr. Senko)
- Make it possible to build and run Nitrate as docker image. PR #180 (Mr. Senko)


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
- Prevent from scrolling page up when show and close tip of environment group (Chenxiong Qi)
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
- TCMS-541 move javascript code of template files into js files as many as possible
- TCMS-545 with the help of template engine(Handlebars.js), get rid of html snippets in js files
- TCMS-663 [RFE][test run] User must click 'show all' link to confirm whether there are comments to a caserun in run detail page.
- TCMS-666 [RFE][test run]When add issue_id to caserun, checked the option 'check to add Test Cases to BZ', system does not sync case_id to bugzilla.
- TCMS-688 Write unit test for xmlrpc.api.testplan and QuerySetBasedSerializer
- TCMS-704 Replace data grid with data table on search plan/run/cases page
- TCMS-714 [TestPlan] The plan name is invisible when the name contains java script contents.
- TCMS-702 Unit test for XMLRPC serializer method
- TCMS-659 Remove code that has already no effective in current TCMS feature
- TCMS-542 rewrite the js code for dom manipulation with jquery and jquery ui, remove prototype.js
- TCMS-549 rewrite the js code for event binding with jquery, remove contorls or effects based on prototype.js
- TCMS-184 Remove the outdate install section
- TCMS-716 [Add cases to run]There are js errors when expanding the case details in the assign case page.
- TCMS-717 [Search Cases]There is a js error in the console when clicking the Search Cases in the Testing tab.
- TCMS-748 Security check via Revok test

3.8.10-2 (Aug 27 2014)
----------------------

- Bug 1133483 - Unable to clone runs in TCMS
- Bug 1133912 - Script injection in notes field
- Bug 1134166 - [test plan] when user remove tag at reviewing case tag in test plan detail page, system returns 500 error

3.8.10-1 (Aug 18 2014)
----------------------

- Bug 1039495 - [test run][export to xml]If a case related many bugs in a run, when export the run to xml, the file only show the latest bug for this case.
- Bug 1129058 - [TestPlan|Add cases] The browser has no response and is in dead after selecting all the selected cases
- Bug 1130903 - [xmlrpc]User can not filter case via estimated_time when invoke TestCase.filter_count method.
- Bug 1130933 - [xmlrpc] User can not update estimated_time to 0s when invoke TestRun.update method.
- Bug 1130961 - [TestPlan|Components] Can't remove all the default components of one test plan at one time
- Bug 1130966 - [xmlrpc][document] The format of estimated_time for related methods should be consistent.
- Bug 1131885 - [XML-RPC] The Texts don't trim the spaces and record them as new versions when invoking the TestCase.store_text() and TestPlan.store_text()
- TCMS-284 [Performance] Production Apache ssl_access_log report some resources(such as css,js,pic etc) can not found(HTTP 404) (RHBZ:1035958)
- TCMS-371 [Performance Test][Reporting Custom] The First Slow Query on the Top Slow Queries found on prod evn (2014-06-05 to 2014-06-12)
- TCMS-425 TestRun & TestCase estimated_time modify
- TCMS-463 [Performance]Reporting Custom Section Optimize
- TCMS-464 [Performance]Reporting Testing Report Section Optimize
- TCMS-478 [xmlrpc]Invoke TestCase.calculate_total_estimated_time with a invalid input, system returns total_estimated_time 00:00:00 not 400 error. (RHBZ:1102459)
- TCMS-480 Enable system-wide cache mechanism to support caching (RHBZ:1027589)
- TCMS-481 [xmlrpc]The result for xmlrpc method TestCase.calculate_average_estimated_time is wrong. (RHBZ:1099312)
- TCMS-482 TestPlan.update does not support 'owner' update (RHBZ:1023679)
- TCMS-484 [test run] If a run has multiple Environments, clone this run, the new run only clone the latest Environment. (RHBZ:1112561)
- TCMS-485 [xmlrpc]when invoke TestCase.link_plan method, the 404 error message lack description. (RHBZ:1112967)
- TCMS-486 [RFE] Suggest improve "Testing Report" generating for large data query (RHBZ:870384)
- TCMS-487 [RFE]: Add test case to the plan by ID (number) (RHBZ:869952)
- TCMS-488 [XMLRPC] List all the methods related to "is_active"field which all needed to be fixed (RHBZ:1108009)
- TCMS-489 [test case]A bug belongs to Run A and Run B for the same case, remove this bug from Run A in case detail page, the bug for Run B is removed as well. (RHBZ:1094603)
- TCMS-492 replace TestRun.is_current with front-end control, and remove operation code against TestRun.is_current in view
- TCMS-493 fix that two requests are emit after change a case run's status
- TCMS-494 Build base infrastructure of unit test
- TCMS-495 Optimize operations on test_case_texts
- TCMS-496 rewrite the ajax style code snippets with jquery
- TCMS-498 [TestCaseRun | Add bug] The added jira bugs don't display in the case run but actually they are added in the xml file. (RHBZ:1119666)
- TCMS-499 [DB] Fix errors when syncdb
- TCMS-500 [Cache] Cache part sections of pages
- TCMS-512 [XML-RPC] TestCase.calculate_total_estimated_time() doesn't work (RHBZ:857831)
- TCMS-513 [Performance] TCMS Reporting respond slowly and cause MySQL server high CPU usage (RHBZ:1029267)
- TCMS-514 [XML-RPC] TestCase.calculate_average_estimated_time() doesn't work (RHBZ:857830)
- TCMS-515 [TestRun][RemoveCase]Remove case into creating test run,the test run's estimated time didn't sync with its cases totally estimate time (RHBZ:849066)
- TCMS-516 [xmlrpc] Can not add cases to the runs with calling the TestRun.add_cases() method (RHBZ:1119224)
- TCMS-551 [test run] After updating the Environment value in test run detail page, user can not remove the changed environment. (RHBZ:1124210)
- TCMS-552 [xmlrpc][document] The example for TestRun.get_test_case_runs method still support is_current parameter. (RHBZ:1126398)
- TCMS-553 [Testing report] Generate testing report By Case Priority, the Priority order for different builds were different. (RHBZ:1125828)
- TCMS-554 [testing report] If all plans belongs to a product have plan tag, system display 'untagged' in tag list in testing report by Plan's Tag (RHBZ:1125815)
- TCMS-555 [Testing report] Generate testing report by Plan's Tag Per Tag View, the caserun's count for idle status was wrong. (RHBZ:1125214)
- TCMS-556 [Testing report] Generate testing report By Plan's Tag Per Tag View, the total caserun's count statistic the duplicate caseruns. (RHBZ:1125821)
- TCMS-557 [TCMS-495 | Texts]Texts of test case and test plan don't support Chinese characters (RHBZ:1126790)
- TCMS-559 [testing report] the link on Paused status in testing report generated by Case-Run Tester was wrong. (RHBZ:1126353)
- TCMS-560 [testing report] Generate testing report by Case-Run Tester, the run's count was wrong. (RHBZ:1126359)
- TCMS-569 [testing report]Generate testing report By Plan's Tag Per Tag View, click link on caserun status to access caserun list, system returns 500 error. (RHBZ:1127621)
- TCMS-570 [TCMS-487| Add cases] Make sure the cases which had been added to the plan can't be searched by case id (RHBZ:1127522)
- TCMS-571 [test case]when create case without estimated_time, system can not save the case. (RHBZ:1126322)
- TCMS-572 [xmlrpc] Do not change the content of plan's text, invoke TestPlan.store_text twice, system will save the content twice with same checksum (RHBZ:1127194)
- TCMS-573 [test plan] If clone case with Create a Copy Settings, system will go to 500 error page. (RHBZ:1126304)
- TCMS-574 [xmlrpc] Invoke TestCase.get_text to get a nonexistent version, system returns 500 error. (RHBZ:1127198)
- TCMS-575 [clone test run] The estimated time format is different with input by manual (RHBZ:1126300)
- TCMS-585 Search cases lead memory leak in production server
- TCMS-619 [XMLRPC] default_product_version is missed in the response from TestPlan
- TCMS-96 [test plan][add child node]When add child note to plan with a nonexistent plan id, the submit btn in the warning form has no effect. (RHBZ:1038950)
- TCMS-98 [test run][add bug]Add reduplicative bug to case in the run page, the content of the warning is incorrect. (RHBZ:1039408)

3.8.9-3 (Aug 11 2014)
---------------------

- Hotfix XMLPRC backward-compatibility broken

3.8.9-2 (Aug 01 2014)
---------------------

- TCMS-538 Solve inconsistent data of product_version field in production database.

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

- Bug 1034100 - [Performance] opening plan/id/chooseruns page causes Python interpreter consumes very hight, around 100%, CPU usage
- TCMS-171 [BZ 866974] Provide TestPlan.{add,get,remove}_component
- TCMS-177 It takes over one min to mark one case to pass in test case run.
- TCMS-186 Too slow when create test run
- TCMS-187 [Performance] Loading test case when expand a test case pane in Cases and Reviewing Cases tabs in a test plan page is too slow.
- TCMS-188 [Performance] Loading test case when expand a test case pane in test run page is too slow
- TCMS-194 [Performance] Expand a plan to display case run list in Case Runs tab in a case page
- TCMS-195 [Performance] Expand a case run from case run list in Case Runs tab in a case page
- Using VERSION.txt file instead of writing version into tcms module directly

3.8.6-5 (Apr 01 2014)
----------------------

- Bug 1082150 - Backward-incompatible change in TestRun.get_test_case_runs()

v3.8.4 (Sep 17 2013)
--------------------
- Fixed bug # 1005797 - [RFE] Add a column with number of comments into Case Runs table
- Fixed bug # 921930 - Date format of attached log links is incorrect

v3.8.2 (Jul 25 2013)
--------------------
- Fixed bug # 988332 - Added one permission protected XMLRPC API to add group for a user.

v3.5 (Jul 11 2011)
------------------
- Fixed bug # 545082 - Test case sort order is shared across plans for cloned cases
- Fixed bug # 589633 - Not able to change author of plan
- Fixed bug # 646325 - [FEAT]cases link doesn't link to the special cases
- Fixed bug # 657160 - [TCMS3.2-2][RFE]Add tips after saving the basic information in the home page (Nitrate 3.2-2)
- Fixed bug # 658339 - [TCMS3.2-2]The "Upload" button is stealing the function of "Create test plan" button when create new test plan
- Fixed bug # 661613 - [Test Plan]Click "Upload" button without browse the attachment will report 404 error
- Fixed bug # 664700 - [FEAT] TCMS - NitrateXmlrpc: add method for new Product version creation
- Fixed bug # 665937 - cancel all the runs you want to clone will turn to the err page
- Fixed bug # 667584 - There is a Error when exporting Test Plan without choose a plan
- Fixed bug # 668323 - add build with non-English name succeeds but warning appears
- Fixed bug # 670996 - Sorting on test plan results page only sorts that page instead of all the results
- Fixed bug # 671457 - [RFE] removal confirmation dialogs should contain number of removed items
- Fixed bug # 672415 - Add a child node to a plan, input non-numbers, causing a dead loop
- Fixed bug # 673421 - Sometimes "file a bug on bugzilla" function doesn't work
- Fixed bug # 675096 - [RFE] chart showing success rate of test-plan-runs
- Fixed bug # 678052 - Tag link causes some nonsense text issues
- Fixed bug # 678203 - [test plan]The product version is not inconsistency in test plan
- Fixed bug # 678220 - [Basic Information]Can not save chinese name in basic information
- Fixed bug # 678465 - [Bookmarks]The box also be checked after delete
- Fixed bug # 678468 - [Bookmarks]There is no warning UI when delete bookmark without any choice
- Fixed bug # 678513 - [Search Plan]there is UnicodeEncodeError when searching plan via chinese tag
- Fixed bug # 678962 - [Component]Suggest pop-up the confirm UI when remove component
- Fixed bug # 678975 - [tag]The link of tag list cause the filter is not correctly
- Fixed bug # 679242 - [Test Case]Click "Upload" button without browse the attachment will report 404 error
- Fixed bug # 679243 - [Test Plan][RFE]Suggest to add the back button when add attachment in test plan
- Fixed bug # 679662 - [Clone Case]The "Autoproposed" can not be clone to the new case
- Fixed bug # 679663 - [Clone case]Can not select "Use the same Plan" after save the clone case without any plan
- Fixed bug # 679675 - [Test Run]There is a UnicodeEncodeError when add a chinese tag
- Fixed bug # 680379 - [Reporting]Click the plan number the result is not correct
- Fixed bug # 681328 - Filters are reset when cases are reordered
- Fixed bug # 682077 - [Quick search]quick search run,it goes to a error page.
- Fixed bug # 690057 - [test run]the test case detail will be auto updated without click update
- Fixed bug # 691413 - Reporting -> Custom page starts with 'No builds found with search condition.'
- Fixed bug # 693281 - Web UI: drop down / list fields' values should be sorted alphabetically
- Fixed bug # 697252 - TCMS - nitrate xmlrpc: failed to attach bug info to TestCaseRun
- Fixed bug # 701591 - [Test case]Suggest "update component"should be "Add component" in test case and del the "remove" button
- Fixed bug # 701697 - Email notification has syntactical error (EN version) - new test run created
- Fixed bug # 703718 - [Usability] improve the layout the test case-run in run
- Fixed bug # 704101 - [Test Case] export test case without select any one will generate an error XML
- Fixed bug # 705983 - [report] product overview tab title can't be seen because the font is white.
- Fixed bug # 706062 - bugs shown in testcase detail
- Fixed bug # 707455 - [Test run]Can not re-order test cases in test run
- Fixed bug # 708883 - Click Bug Id could not link to bugzilla
- Fixed bug # 709764 - caserun link doesn't focus case in run
- Fixed bug # 710104 - Ordered list function of WYSIWYG: Numbers are not displayed.
- Fixed bug # 711005 - Return all relevant information in xml-rpc call
- Fixed bug # 711657 - The printable GUI can't show correctly
- Fixed bug # 712772 - [Test case]Export testcase without select any one
- Fixed bug # 712789 - Cannot open attachments
- Fixed bug # 713662 - [Extremely Urgent] Some test plans lost all|most|some test cases this afternoon.
- Fixed bug # 715209 - 100% Completion graphical progress bar does not look 100%, it has still a gap to be filled.
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
- Fixed bug # 691412 - [TCMS] [Reporting] : no way to search according to case priority or plan tags
- Fixed bug # 691695 - [TCMS] [Reporting] : generate reports per user
- Fixed bug # 691696 - [TCMS] [Reporting] : generate reports for few build [multi selection]
- Fixed bug # 706839 - [Advanced search]When click link "Return to homepage", come out warning "Bad Request"
- Fixed bug # 707243 - bug links don't work

v3.4 (May 24 2011)
------------------
- Fixed bug #690423 - [xmlrpc] - xmlrpc loses connection to the server after a short timeout
- Fixed bug #593760 - xmlrpc doc doesn't match actual behavior: TestRun.update
- Fixed bug #593805 - xmlrpc Testcase.update fails when using certain arguments
- Fixed bug #662885 - Product version update failed for run 15325.
- Fixed bug #656098 - [FEAT] Relationship query
- Fixed bug #699311 - [New Plan]There aren't permissions to add "classification", "products", "versions"
- Fixed bug #705975 - [Printable copy]Can not printable copy one/more/all plan(s) in search list
- Fixed bug #705974 - [Export plan]Can not export one/more/all plan(s) in search list
- Fixed bug #697577 - pattern ID pointing to wrong place
- Fixed bug #682081 - [Test Case]Create a case with all fields,The UI is mess.
- Fixed bug #603622 - TestCase.add_component: adding already attached component results in traceback
- Fixed bug #637715 - TestCaseRun.update() should set tester to authenticated user
- Fixed bug #634295 - [FEAT]Bulk status change.
- Fixed bug #683844 - Update TinyMCE editor to recent version
- Fixed bug #683074 - One bug listed many times
- Fixed bug #669049 - [RFE] Editing a testrun - add a build.
- Fixed bug #644748 - Nitrate XML-RPC Service: failed to create new TestRun using the 'TestRun.create' verb.
- Fixed bug #587716 - FEAT - Need a new API call - to return a user object based on user ID's - such as tested_by_id
- Fixed bug #593091 - Programmatic access to TCMS via API requires user's Kerberos username/password
- Fixed bug #583136 - testplan.filter() returns plan objects that lack complete information
- Fixed bug #696047 - Default font size is too small in editor.
- Fixed bug #672124 - Default tester does not have permission to execute test run.
- Fixed bug #678184 - [Test Run]There are error info sorting test case in test run
- Fixed bug #680064 - [Test Run]The product version will be added to build list when Create New Test Run
- Fixed bug #690741 - [test run]Suggest can not remove the bug from other run
- Fixed bug #680032 - [Clone case][RFE]Add "cancel" button in mulitple clone page
- Fixed bug #680317 - [Test Run]The update function is invalid in test case run
- Fixed bug #680318 - [Create run]There is Warning about Data truncated when create run with more than 255 in summary
- Fixed bug #680380 - [Reporting]The warning UI is jumbled after select without choose product
- Fixed bug #679638 - [Test case]Print test case without choose any one is the same to choose all
- Fixed bug #698035 - [Sentmail]the reviewer received the TCMS mail rather than stage
- Fixed bug #593818 - Setting status=1 in TestRun.update should leave it in STOPPED state, but UI shows RUNNING
- Fixed bug #598882 - Changing status icon to 'start' or 'in progress' ("play" icon) jumps to next test case
- Fixed bug #663364 - [FEAT]Unable to search for multiple authors.
- Fixed bug #665052 - [FEAT] add test-case/test-run creation/completion date search criteria
- Fixed bug #671454 - [FEAT] search test-case by script
- Fixed bug #684804 - service error when accessing test-case from plan it is not a member of
- Fixed bug #615914 - [FEAT] searches with multiple products selected
- Fixed bug #670759 - [FEAT]Add a search item "Case Id"
- Fixed bug #680430 - [FEAT] search for test-cases from different products
- Fixed bug #653919 - [FEAT] filtering case-runs according to test-plan
- Fixed bug #542968 - [FEAT]Nitrate doesn't allow group operations on test case runs
- Fixed bug #564316 - [FEAT] tag searching - bugzilla-like categories or negative searching & regexps

v3.3-4 (Mar 3 2011)
-------------------
- Fixed bug 681156 - [Test Plan]Can not expand all the test case in test plan.
- Fixed Bug 679677 - [Test Run]The button should be "cancel" in Property page.
- Fixed Bug 672495 - Old test run shows updated case information but its text version is unchanged.

v3.3-3 (Feb 25 2011)
--------------------
- Fixed bug 680315 - [Reporting]Open a product will lead to the error page.
- Fixed bug 680321 - [Test Run]Click "View My Assigned Runs" will list all runs
- Fixed bug 627236 - s/2009/2010/ orequivalent of date in page footer
- Fixed bug 680322 - New: [spelling mistake]"Highligt" should be "Highlight"
- Fixed Bug 680059 - [Test Run]The total number of test case run is NULL
- remove "running date" add "run date"
- Fixed bug 676259 - [FEAT] Need to get a break out of manual vs auto in the tcms reporting section
- Fixed bug 678643 - TestPlan.get_text - multiple failures
- Fixed bug 674754 - [xmlrpc] TestRun.create() fails when list of tags provided
- Fixed bug 676590 - In run execute page, 'expand all' generates tons of http requests

v3.3-2 (Feb 15 2011)
--------------------
- Fixed bug 664025 - TCMS main check box to control test cases doesn't work
- Fixed bug 658372 - Cannot select "Product Version" when clone multiple test plans
- Fixed bug 667304 - Click "Build" label, it won't be sorted by build
- Fixed bug 654533 - [TCMS]Document Version in test plan on opera browser
- Fixed bug 672873 - xml export can't be parsed
- Fixed bug 664743 - [RFE] supply existing bugs when marking test-case-run as failed
- Fixed bug 672857 - Typo in error message when a test plan hasn't been
- Fixed bug 657474 [TCMS3.2-2]List the runs which have not environment
- Fixed bug 649293 - Make the case run "notes" field visible in the run
- Fixed bug 643324 - Provide a bit more space for the test run notes
- Fixed bug 653815 - Unable to re-order test cases in test run
- Fixed bug 658475 - The bug can not be deleted inside the run
- Fixed bug 672622 - product version gets set to "unused" when editing a plan

v3.3-1 (Jan 24 2011)
--------------------
- Fixed bug 661951 - Messed-up warning message pop up when clicking Add without entering Bug ID
- Fixed bug 665945 - run export button dosn't work
- Fixed bug 667293 - The first product is the default product.
- Fixed bug 665934 - choose no plan to "Printalbe Copy"
- Fixed Bug 654953 - [RFE] Report an expanded list of Test Cases by Tag
- Fixed bug 664467 - TCMS: cells overlapping when using long name for test case summary
- Fixed bug 662944 - Resort case run is broken in Firefox
- Fixed bug 642644 - update nitrate.py to work with the latest xmlrpclib
- Fixed bug 578717 - [REF] Provide filter in test run
- Fixed bug 653812 - Filtering test case runs
- Fixed bug 534063 - [RFE] Allow sorting / filtering test cases while executing the test run
- Fixed bug 660234 - Add links to IDLE, PASSED, WAIVED items in report table again
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
- Fixed UI Bug #657452 - [TCMS3.2-2]put mouse on the status buttons and no tips …
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
- Fixed #635931 - [TCMS]The blank row in Status' drop-down box of Search test Runs
- Fixed UI Bug #637471 - [TCMS][REF]The style in the home page
- Completed Feature #637271 - Provide an XMLRPC function for adding a test case run comment
- Makes Django 1.2 compatible
- Add csrf to templates/admin pages for Django 1.2
- Fixed #638639 Test run report "Finished at" field shows "Notes" content
- Fixed UI Bug #638019 -[REF]Test Runs in the home page
- Bug UI Bug #641252 - [TCMS][REF]"Testing Cases" to "Cases" in REPORTING
- Refined the js, split the case to confirmed cases and reviewing cases
- Fixed #637474 - [TCMS][REF]The sort of "Plan Type" data and the sort of "Environment Group" data in Search Plan page.
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
- Fixed #644748 - Nitrate XML-RPC Service: failed to create new TestRun using the 'TestRun.create' verb
- Completed basic info editing/viewing in profile
- Add the title/nav/footer to 404 & 500 error page
- Add NEED_UPDATE status to test case status
- Fixed UI Bug #629122 - [REF] Display test case notes when expanding a test case
- Fixed UI Bug #641790 - [TCMS]No warning after inputting "1.1" in the sort of case
- Fixed UI Bug #643303 - [RFE] test-run report - show bugs near corresponding test-cases
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
- Fixed #646399 - In case permission are not granted, you are asked for login credentials that are never accepted.
- Fixed redirect to review cases after case creation
- Refined the delete comment feature
- Fixed log display in details page
- Fixed auto case expanding in run page
- Fixed #637870 - The sum of the percentage of the test status categories on the overall report for a given build do not sum to 100%
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
- Fixed UI Bug #625797 - test case run history should display test run summaries
- Fixed #626638 - Product version is not copied from the original when …
- Fixed #627235 - Adding a build requires reloading page.
- Fixed UI Bug #629977 - test-run report does not contain test-run name
- Completed feature #542660 - TCMS: [FEAT] - allow to add sub test suite for test plan
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
- Fixed UI Bug #610127 - show/highlight test-case-runs assigned to me when executing …
- Fixed UI Bug #612880 - Need total number for filter out result
- Completed feature #607844 - (RFE) Flag tests which require the IEEE Test …
- Completed Feature #587143 - [FEAT] Have a default component when creating …
- Move the compoent of the case to be a tab
- Use the updateObject() function to reimplemented multiple operations.

v3.0.3-2.svn2859 (Jun 28 2010)
------------------------------
- Fixed bug #604860. Modify ComponentAdmin?'s search_fields from (('name',)) …
- Update the plan list & case list & run list
- Update the case run list
- Change from_config()'s return value from Nitrate to NitrateXmlrpc?
- Fixed #606751 - grammar error on dashboard
- Fixed #605918 - Submitting larger comments fails
- Completed edit environment in run page
- Use updateObject() function to modify the sortkey for caserun
- Fixed create case failed issue
- Completed feature #604860 - further improvement Add 'pk' for each item under …
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
- Fixed #593091 - Programmatic access to TCMS via API requires user's Kerberos username/password
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
- Completed FEAT UI Bug #539077 - Provide an overall status on main test run page
- Completed FEAT BUg #574172 - If you sort a column in a plan, the filter options …
- Fixed Bug #567495 - Sort by category for 898 test cases results in 'Request …
- Completed FEAT #597705 - TCMS: Unknown user: when user name have space before or …
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
- Product.filter_categories(), Product.filter_components(), Product.filter_versions(),
- Product.get_component(), Product.get_tag(), Product.get_versions(),
- Product.lookup_id_by_name(), TestCase.calculate_average_estimated_time(),
- TestCase.calculate_total_estimated_time(), User.filter(), User.get(),
- User.update().
- Fixed UI bugs: #590647, #583908, #570351, #588970, #588565, #578828, #562110,
- #582958, #542664.
- Fixed app bugs: #582517, #582910, #584838, #586684, #584342, #578828
- #577820, #583917, #562110, #580494, #570351, #589124, #577130, #561406, #586085,
- #588595, #560791, #584459.

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
- [2152] Fixed bug #530478 - Case run case_text_version is 0 cause to file bug crash
- [2154] Fixed bug #538747
- [2156] Use QuerySet update function to batch modify the database
- [2158] Fixed bug #540794 - [FEAT]It should stay in the same tab/page after refreshing
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
- KNOWN ISSUE: Search case to add to plan just complete the page design, is waiting for logic function.

v2.0-2.svn1938 (Sep 30 2009)
----------------------------
- Rewrite assign case page
- Rewrite attachment implementation
- Search with environment is available
- Fixed app bugs:
- Fixed #524578 - The Product version will display after finish searching plans
- Fixed #524568 - Cannot reset the status of test cases when the status is "Passed" or "Failed"
- Fixed #524534 - Can't add a new test case
- UI Bugs:
- Fixed #524530 - Please adjust the Next button in create new plan page0
- Fixed #525044 - The buttons are not aligned and missing some checkboxes when searching cases
- Fixed #524568 - Cannot reset the status of test cases when the status is "Passed" or "Failed"
- Fixed #524140 - Cannot create test plan when the uploaded plan document's type is HTML
- Fixed #525614 - The label that counts the number should at the same place on every ADMIN's sub-tab
- Fixed #524777 - [FEAT]It should have breadcrumbs on Admin tab have added breadcrumb to admin page
- Fixed #525630 - The calendar and clock icon should be kept on the same line with date and time
- Fixed #525830 - The same buttons aligned in different tabs should keep consistent
- Fixed #525606 - "Is active" should be kept on the same line with its check-box

v2.0-2.svn1898 (Sep 23 2009)
----------------------------
- Feature:
- Completed environment element modfiy/delete feature in admin
- Fixed #525039 - [FEAT]It should let users add notes and set status of test cases even when the status of the test run is "Finished"
- UI Bugs:
- Fixed #521327 - Test Plan Document translation not quite right
- Fixed #524230 - can't change the "automated" field of a test case
- Fixed #524536 - Suggest to adjust the add new test case page width and the button "Add case"
- Fixed #524530 - Please adjust the Next button in create new plan page
- Fixed #518652 - can't remove test case from a plan
- Fixed #524774 - [FEAT]It should have a title on each of the add "Admin=>Management" webpage
- Fixed #525044 - The buttons are not aligned and missing some checkboxes when searching cases
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
- substitute RPM metadata into the page footer so that it always shows the exact revision of the code
- bump to svn revision 1525

v0.16-3.svn1487 (Mar 12 2009)
-----------------------------
- drop the dist tag

v0.16-2.svn1487 (Mar 12 2009)
-----------------------------
- add build-requires on Django to try to get pylint to work (otherwise: tcms/urls.py:11: [E0602] Undefined variable 'patterns')

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
