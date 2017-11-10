import random

from django import test

import tcms_api


class BaseAPIClient_TestCase(test.TestCase):
    """
        Bring up a local Django instance and
        prepare test data - create Test Cases, Test Plans and Test Runs
    """

    # how many test objects to create
    num_cases = 1
    num_plans = 1
    num_runs = 1

    @classmethod
    def setUpTestData(cls):
        cls.MASTER_TESTPLAN_NAME = "Master Test Plan"
        cls.PRODUCT = tcms_api.Product(name="RHEL Tests")
        cls.VERSION = tcms_api.Version(product=cls.PRODUCT, version="unspecified")
        cls.PLANTYPE = tcms_api.PlanType(name="Function")
        cls.CATEGORY = tcms_api.Category(category="Regression", product=cls.PRODUCT)
        cls.CASESTATUS = tcms_api.CaseStatus("CONFIRMED")
        cls.BUILD = tcms_api.Build(product=cls.PRODUCT, build="unspecified")

        cls.TAGS = [tcms_api.Tag(id) for id in range(3000, 3200)]
        cls.TESTERS = [tcms_api.User(id) for id in range(1000, 1050)]

        # Create test cases
        cls.cases = []
        for case_count in range(cls.num_cases):
            testcase = tcms_api.TestCase(
                name="Test Case {0}".format(case_count + 1),
                category=cls.CATEGORY,
                product=cls.PRODUCT,
                summary="Test Case {0}".format(case_count + 1),
                status=cls.CASESTATUS)
            # Add a couple of random tags and the default tester
            testcase.tags.add([random.choice(cls.TAGS) for counter in range(10)])
            testcase.tester = random.choice(cls.TESTERS)
            testcase.update()
            cls.cases.append(testcase)

        # Create master test plan (parent of all)
        cls.master = tcms_api.TestPlan(
            name=cls.MASTER_TESTPLAN_NAME,
            product=cls.PRODUCT,
            version=cls.VERSION,
            type=cls.PLANTYPE)
        tcms_api.info("* {0}".format(cls.master))
        cls.master.testcases.add(cls.cases)
        cls.master.update()

        # Create child test plans
        for plan_count in range(cls.num_plans):
            testplan = tcms_api.TestPlan(
                name="Test Plan {0}".format(plan_count + 1),
                product=cls.PRODUCT,
                version=cls.VERSION,
                parent=cls.master,
                type=cls.PLANTYPE)
            # Link all test cases to the test plan
            testplan.testcases.add(cls.cases)
            testplan.update()
            tcms_api.info("  * {0}".format(testplan))

            # Create test runs
            for run_count in range(cls.num_runs):
                testrun = tcms_api.TestRun(
                    testplan=testplan,
                    build=cls.BUILD,
                    product=cls.PRODUCT,
                    summary="Test Run {0}".format(run_count + 1),
                    version=cls.VERSION)
                tcms_api.info("    * {0}".format(testrun))
