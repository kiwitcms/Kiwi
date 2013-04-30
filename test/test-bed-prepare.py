#!/usr/bin/python
""" Prepare test bed - create Test Cases, Test Plans and Test Runs """

import nitrate
import random
import optparse

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Global Constants
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MASTER_TESTPLAN_NAME = "Master Test Plan"
PRODUCT = nitrate.Product(name="RHEL Tests", version="unspecified")
VERSION = nitrate.Version(product=PRODUCT, version="unspecified")
PLANTYPE = nitrate.PlanType(name="Function")
CATEGORY = nitrate.Category(category="Regression", product=PRODUCT)
CASESTATUS = nitrate.CaseStatus("CONFIRMED")
BUILD = nitrate.Build(product=PRODUCT, build="unspecified")

TAGS = [nitrate.Tag(id) for id in range(3000, 3200)]
TESTERS = [nitrate.User(id) for id in range(1000, 1050)]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Parse Options
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def parse_options():
    parser = optparse.OptionParser(
            usage = "test-bed-prepare [--plans #] [--runs #] [--cases #]",
            description=__doc__.strip())
    parser.add_option("--plans",
            dest = "plans",
            type = "int",
            action = "store",
            default = 1,
            help = "create specified number of plans")
    parser.add_option("--runs",
            dest = "runs",
            type = "int",
            action = "store",
            default = 1,
            help = "create specified number of runs")
    parser.add_option("--cases",
            dest = "cases",
            type = "int",
            action = "store",
            default = 1,
            help = "create specified number of cases")
    return parser.parse_args()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Main
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":
    (options, arguments) = parse_options()

    # Create test cases
    cases = []
    for case_count in range(options.cases):
        testcase = nitrate.TestCase(
                name="Test Case {0}".format(case_count + 1),
                category=CATEGORY,
                product=PRODUCT,
                summary="Test Case {0}".format(case_count + 1),
                status=CASESTATUS)
        # Add a couple of random tags and the default tester
        testcase.tags.add([random.choice(TAGS) for counter in range(10)])
        testcase.tester = random.choice(TESTERS)
        testcase.update()
        cases.append(testcase)

    # Create master test plan (parent of all)
    master = nitrate.TestPlan(
            name=MASTER_TESTPLAN_NAME,
            product=PRODUCT,
            version=VERSION,
            type=PLANTYPE)
    nitrate.info("* {0}".format(master))
    master.testcases.add(cases)
    master.update()

    # Create child test plans
    for plan_count in range(options.plans):
        testplan = nitrate.TestPlan(
                name="Test Plan {0}".format(plan_count + 1),
                product=PRODUCT,
                version=VERSION,
                parent=master,
                type=PLANTYPE)
        # Link all test cases to the test plan
        testplan.testcases.add(cases)
        testplan.update()
        nitrate.info("  * {0}".format(testplan))
        for run_count in range(options.runs):
            # Create test runs
            testrun = nitrate.TestRun(
                    testplan=testplan,
                    build=BUILD,
                    product=PRODUCT,
                    summary="Test Run {0}".format(run_count + 1),
                    version=VERSION)
            nitrate.info("    * {0}".format(testrun))
