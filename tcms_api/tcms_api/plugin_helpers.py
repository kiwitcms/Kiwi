# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

import os

from . import TCMS


class Backend:
    """
        Facilitates RPC communications with the backend and implements
        behavior described at:
        http://kiwitcms.org/blog/atodorov/2018/11/05/test-runner-plugin-specification/

        This class is intended to be used by Kiwi TCMS plugins implemented in
        Python. The plugin will call::

            backend = Backend()
            backend.configure()

            ... parse test results ...

            test_case_id = backend.test_case_get_or_create(<description>)
            backend.add_test_case_to_plan(test_case_id, backend.plan_id)
            test_case_run_id = backend.add_test_case_to_run(test_case_id, backend.run_id)
            backend.update_test_case_run(test_case_run_id, <status_id>, <comment>)

        :param prefix: Prefix which will be added to TestPlan.name and
                       TestRun.summary

                       .. versionadded:: 5.2
        :type prefix: str
    """

    _statuses = {}
    _cases_in_test_run = {}

    def __init__(self, prefix=''):
        """
            :param prefix: Prefix which will be added to TestPlan.name and
                           TestRun.summary

                           .. versionadded:: 5.2
            :type prefix: str
        """
        self.prefix = prefix

        self.rpc = None
        self.run_id = None
        self.plan_id = None
        self.product_id = None
        self.category_id = None
        self.priority_id = None
        self.confirmed_id = None

    def configure(self):
        """
            This method is reading all the configs from the environment
            and will create necessary TestPlan and TestRun containers!

            One of the main reasons for it is that
            :py:attr:`tcms_api.tcms_api.TCMS.exec` will try to connect
            immediately to Kiwi TCMS!

            .. important::

                Test runner plugins **must** call this method after
                initializing the backend object and **before** calling
                any of the other methods!
        """
        self.rpc = TCMS().exec

        self.run_id = self.get_run_id()
        self.plan_id = self.get_plan_id(self.run_id)
        self.product_id, _ = self.get_product_id(self.plan_id)

        self.category_id = self.rpc.Category.filter({
            'product': self.product_id
        })[0]['id']
        self.priority_id = self.rpc.Priority.filter({})[0]['id']
        self.confirmed_id = self.rpc.TestCaseStatus.filter({
            'name': 'CONFIRMED'
        })[0]['id']

    def get_status_id(self, name):
        """
            Get the PK of :class:`tcms.testruns.models.TestCaseRunStatus`
            matching the test execution status.

            .. important::

                Test runner plugins **must** call this method like so::

                    id = backend.get_status_id('FAILED')

            :param name: :class:`tcms.testruns.models.TestCaseRunStatus` name
            :type name: str
            :rtype: int
        """
        if name not in self._statuses:
            self._statuses[name] = self.rpc.TestCaseRunStatus.filter({
                'name': name
            })[0]['id']

        return self._statuses[name]

    def get_product_id(self, plan_id):
        """
            Return a :class:`tcms.management.models.Product` PK.

            .. warning::

                For internal use by `.configure()`!

            :param plan_id: :class:`tcms.testplans.models.TestPlan` PK
            :type plan_id: int
            :rtype: int

            Order of precedence:

            - `plan_id` is specified, then use TestPlan.product, otherwise
            - use `$TCMS_PRODUCT` as Product.name if specified, otherwise
            - use `$TRAVIS_REPO_SLUG` as Product.name if specified, otherwise
            - use `$JOB_NAME` as Product.name if specified

            If Product doesn't exist in the database it will be created with the
            first :class:`tcms.management.models.Classification` found!
        """
        product_id = None
        product_name = None

        test_plan = self.rpc.TestPlan.filter({'pk': plan_id})
        if test_plan:
            product_id = test_plan[0]['product_id']
            product_name = test_plan[0]['product']
        else:
            product_name = os.environ.get('TCMS_PRODUCT',
                                          os.environ.get('TRAVIS_REPO_SLUG',
                                                         os.environ.get(
                                                             'JOB_NAME')))
            if not product_name:
                raise Exception('Product name not defined, '
                                'missing one of TCMS_PRODUCT, '
                                'TRAVIS_REPO_SLUG or JOB_NAME')

            product = self.rpc.Product.filter({'name': product_name})
            if not product:
                class_id = self.rpc.Classification.filter({})[0]['id']
                product = [self.rpc.Product.create({
                    'name': product_name,
                    'classification_id': class_id
                })]
            product_id = product[0]['id']

        return product_id, product_name

    def get_version_id(self, product_id):
        """
            Return a :class:`tcms.management.models.Version` (PK, name).

            .. warning::

                For internal use by `.configure()`!

            :param product_id: :class:`tcms.management.models.Product` PK
                               for which to look for Version
            :type product_id: int
            :return: (version_id, version_value)
            :rtype: tuple(int, str)

            Order of precedence:

            - use `$TCMS_PRODUCT_VERSION` as Version.value if specified, otherwise
            - use `$TRAVIS_COMMIT` as Version.value if specified, otherwise
            - use `$TRAVIS_PULL_REQUEST_SHA` as Version.value if specified,
              otherwise
            - use `$GIT_COMMIT` as Version.value if specified

            If Version doesn't exist in the database it will be created with the
            specified `product_id`!
        """
        version_val = os.environ.get(
            'TCMS_PRODUCT_VERSION',
            os.environ.get('TRAVIS_COMMIT',
                           os.environ.get('TRAVIS_PULL_REQUEST_SHA',
                                          os.environ.get('GIT_COMMIT'))))
        if not version_val:
            raise Exception('Version value not defined, '
                            'missing one of TCMS_PRODUCT_VERSION, '
                            'TRAVIS_COMMIT, TRAVIS_PULL_REQUEST_SHA '
                            'or GIT_COMMIT')

        version = self.rpc.Version.filter({'product': product_id,
                                           'value': version_val})
        if not version:
            version = [self.rpc.Version.create({'product': product_id,
                                                'value': version_val})]

        return version[0]['id'], version_val

    def get_build_id(self, product_id, _version_id):
        """
            Return a :class:`tcms.management.models.Build` (PK, name).

            .. warning::

                For internal use by `.configure()`!

            :param product_id: :class:`tcms.management.models.Product` PK
                               for which to look for Build
            :type product_id: int
            :param version_id: :class:`tcms.management.models.Version` PK
                               for which to look for Build
            :type version_id: int
            :return: (build_id, build_name)
            :rtype: tuple(int, str)

            Order of precedence:

            - use `$TCMS_BUILD` as Build.name if specified, otherwise
            - use `$TRAVIS_BUILD_NUMBER` as Build.name if specified, otherwise
            - use `$BUILD_NUMBER` as Build.name if specified

            If Build doesn't exist in the database it will be created with the
            specified `product_id`!

            .. note::

                For `version_id` see https://github.com/kiwitcms/Kiwi/issues/246
        """
        build_number = os.environ.get('TCMS_BUILD',
                                      os.environ.get('TRAVIS_BUILD_NUMBER',
                                                     os.environ.get(
                                                         'BUILD_NUMBER')))
        if not build_number:
            raise Exception('Build number not defined, '
                            'missing one of TCMS_BUILD, '
                            'TRAVIS_BUILD_NUMBER or BUILD_NUMBER')

        build = self.rpc.Build.filter({'name': build_number,
                                       'product': product_id})
        if not build:
            build = [self.rpc.Build.create({'name': build_number,
                                            'product': product_id})]

        return build[0]['build_id'], build_number

    def get_plan_type_id(self):
        """
            Return an **Integration** PlanType.

            .. warning::

                For internal use by `.configure()`!

            :return: :class:`tcms.testplans.models.PlanType` PK
            :rtype: int
        """
        plan_type = self.rpc.PlanType.filter({'name': 'Integration'})
        if not plan_type:
            plan_type = [self.rpc.PlanType.create({'name': 'Integration'})]

        return plan_type[0]['id']

    def get_plan_id(self, run_id):
        """
            If a TestRun with PK `run_id` exists then return the TestPlan to
            which this TestRun is assigned, otherwise create new TestPlan with
            Product and Version specified by environment variables.

            .. warning::

                For internal use by `.configure()`!

            :param run_id: :class:`tcms.testruns.models.TestRun` PK
            :type run_id: int
            :return: :class:`tcms.testplans.models.TestPlan` PK
            :rtype: int
        """
        result = self.rpc.TestRun.filter({'pk': run_id})
        if not result:
            product_id, product_name = self.get_product_id(0)
            version_id, version_name = self.get_version_id(product_id)

            name = self.prefix + 'Plan for %s (%s)' % (product_name, version_name)

            result = self.rpc.TestPlan.filter({'name': name,
                                               'product': product_id,
                                               'product_version': version_id})

            if not result:
                plan_type_id = self.get_plan_type_id()

                result = [self.rpc.TestPlan.create({
                    'name': name,
                    'text': 'Created by tcms_api.plugin_helpers.Backend',
                    'product': product_id,
                    'product_version': version_id,
                    'is_active': True,
                    'type': plan_type_id,
                })]

        return result[0]['plan_id']

    def get_run_id(self):
        """
            If `$TCMS_RUN_ID` is specified then assume the caller knows
            what they are doing and try to add test results to that TestRun.
            Otherwise will create a TestPlan and TestRun in which to record
            the results!

            .. warning::

                For internal use by `.configure()`!

            :return: :class:`tcms.testruns.models.TestRun` PK
            :rtype: int
        """
        run_id = os.environ.get('TCMS_RUN_ID')

        if not run_id:
            product_id, product_name = self.get_product_id(0)
            version_id, version_val = self.get_version_id(product_id)
            build_id, build_number = self.get_build_id(product_id, version_id)
            plan_id = self.get_plan_id(0)
            # the user issuing the request
            user_id = self.rpc.User.filter()[0]['id']

            testrun = self.rpc.TestRun.create({
                'summary': self.prefix + 'Results for %s, %s, %s' % (
                    product_name, version_val, build_number
                ),
                'manager': user_id,
                'plan': plan_id,
                'build': build_id,
            })
            run_id = testrun['run_id']

        # fetch pre-existing test cases in this TestRun
        # used to avoid adding existing TC to TR later
        for case in self.rpc.TestRun.get_cases(run_id):
            self._cases_in_test_run[case['case_id']] = case['case_run_id']

        return int(run_id)

    def test_case_get_or_create(self, summary):
        """
            Search for a TestCase with the specified `summary` and Product.
            If it doesn't exist in the database it will be created!

            .. important::

                Test runner plugins **must** call this method!

            :param summary: A TestCase summary
            :type summary: str
            :return: Serialized :class:`tcms.testcase.models.TestCase`
            :rtype: dict
        """
        test_case = self.rpc.TestCase.filter({
            'summary': summary,
            'category__product': self.product_id,
        })

        if not test_case:
            test_case = [self.rpc.TestCase.create({
                'summary': summary,
                'category': self.category_id,
                'product': self.product_id,
                'priority': self.priority_id,
                'case_status': self.confirmed_id,
                'notes': 'Created by tcms_api.plugin_helpers.Backend',
            })]

        return test_case[0]

    def add_test_case_to_plan(self, case_id, plan_id):
        """
            Add a TestCase to a TestPlan if it is not already there!

            .. important::

                Test runner plugins **must** call this method!

            :param case_id: :class:`tcms.testcases.models.TestCase` PK
            :type case_id: int
            :param plan_id: :class:`tcms.testplans.models.TestPlan` PK
            :type plan_id: int
            :return: None
        """
        if not self.rpc.TestCase.filter({'pk': case_id, 'plan': plan_id}):
            self.rpc.TestPlan.add_case(plan_id, case_id)

    def add_test_case_to_run(self, case_id, run_id):
        """
            Add a TestCase to a TestRun if it is not already there!

            .. important::

                Test runner plugins **must** call this method!

            :param case_id: :class:`tcms.testcases.models.TestCase` PK
            :type case_id: int
            :param run_id: :class:`tcms.testruns.models.TestRun` PK
            :type run_id: int
            :return: :class:`tcms.testruns.models.TestCaseRun` PK
            :rtype: int
        """
        if case_id in self._cases_in_test_run.keys():
            return self._cases_in_test_run[case_id]

        return self.rpc.TestRun.add_case(run_id, case_id)['case_run_id']

    def update_test_case_run(self, test_case_run_id, status_id, comment=None):
        """
            Update TestCaseRun with a status and comment.

            .. important::

                Test runner plugins **must** call this method!

            :param test_case_run_id: :class:`tcms.testruns.models.TestCaseRun` PK
            :type test_case_run_id: int
            :param status_id: :class:`tcms.testruns.models.TestCaseRunStatus` PK,
                              for example the ID for PASSED, FAILED, etc.
                              See :func:`tcms_api.tcms_api.plugin_helpers.Backend.get_status_id`
            :type status_id: int
            :param comment: the string to add as a comment, defaults to None
            :type comment: str
            :return: None
        """
        self.rpc.TestCaseRun.update(test_case_run_id,  # pylint: disable=objects-update-used
                                    {'status': status_id})

        if comment:
            self.add_comment(test_case_run_id, comment)

    def add_comment(self, test_case_run_id, comment):
        """
            Add comment string to TestCaseRun without changing the status

            .. important::

                Test runner plugins **must** call this method!

            :param test_case_run_id: :class:`tcms.testruns.models.TestCaseRun` PK
            :type test_case_run_id: int
            :param comment: the string to add as a comment
            :type comment: str
            :return: None
        """
        self.rpc.TestCaseRun.add_comment(test_case_run_id, comment)
