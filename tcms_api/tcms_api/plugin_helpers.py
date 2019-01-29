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
    """

    _statuses = {}
    _cases_in_test_run = {}

    def __init__(self, prefix=''):
        """
            :param prefix: Prefix which will be added to TestPlan.name and
                           TestRun.summary
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
        if name not in self._statuses:
            self._statuses[name] = self.rpc.TestCaseRunStatus.filter({
                'name': name
            })[0]['id']

        return self._statuses[name]

    def get_product_id(self, plan_id):
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
        # for _version_id see https://github.com/kiwitcms/Kiwi/issues/246
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
        plan_type = self.rpc.PlanType.filter({'name': 'Integration'})
        if not plan_type:
            plan_type = [self.rpc.PlanType.create({'name': 'Integration'})]

        return plan_type[0]['id']

    def get_plan_id(self, run_id):
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
        if not self.rpc.TestCase.filter({'pk': case_id, 'plan': plan_id}):
            self.rpc.TestPlan.add_case(plan_id, case_id)

    def add_test_case_to_run(self, case_id, run_id):
        if case_id in self._cases_in_test_run.keys():
            return self._cases_in_test_run[case_id]

        return self.rpc.TestRun.add_case(run_id, case_id)['case_run_id']

    def update_test_case_run(self, test_case_run_id, status_id, comment=None):
        self.rpc.TestCaseRun.update(test_case_run_id,  # pylint: disable=objects-update-used
                                    {'status': status_id})

        if comment:
            self.rpc.TestCaseRun.add_comment(test_case_run_id, comment)
