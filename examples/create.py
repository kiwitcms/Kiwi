#!/usr/bin/python
"""
Basic Example

Simple example showing the main features of the python-nitrate module.
Covered are testplan, testrun, testcase creation, logging, setting the
log level, cache level and color mode, test case linking, attributes
adjustments and updating the changes to the server.
"""

import nitrate
from nitrate import info, log

# Set log level, cache level and color mode
nitrate.set_log_level(nitrate.LOG_DEBUG)
nitrate.set_cache_level(nitrate.CACHE_OBJECTS)
nitrate.set_color_mode(nitrate.COLOR_AUTO)

# Initialize an existing test plan
info("Initializing an existing test plan")
general_plan = nitrate.TestPlan(3781)
print general_plan

# Logging, catching errors
nitrate.set_log_level(nitrate.LOG_INFO)
info("Initializing a bad test plan")
try:
    log.info("Inspecting the test plan")
    bad_plan = nitrate.TestPlan(1)
    print bad_plan
except nitrate.NitrateError, error:
    log.error("Bad test plan id ({0})".format(error))

# Iterate over all test plan's test cases
info("Inspecting test plan's test cases")
for testcase in general_plan:
    print testcase

# Create a new test plan
info("Creating a new test plan")
release_plan = nitrate.TestPlan(
        parent=general_plan,
        name="python / rhel-6.2.0 / ER#11359",
        type="Release",
        product="Red Hat Enterprise Linux 6",
        version="6.2")

# Link all automated test cases from the general plan
info("Linking automated test cases from the general plan")
for testcase in general_plan:
    if testcase.automated:
        release_plan.testcases.add(testcase)
release_plan.update()

# Create a new test case
info("Creating a new test case")
testcase = nitrate.TestCase(
        summary="New performance test",
        product="Red Hat Enterprise Linux 6",
        category="Performance",
        script="/CoreOS/python/Performance/base")

# Set status, priority, default tester, add tags, attach bugs, link plans
info("Setting status, priority, tester, tags, bugs and plans")
testcase.status = nitrate.CaseStatus("CONFIRMED")
testcase.priority = nitrate.Priority("P1")
testcase.tester = nitrate.User("psplicha")
testcase.tags.add(nitrate.Tag("Tier1"))
testcase.bugs.add(nitrate.Bug(bug=123))
testcase.testplans.add([general_plan, release_plan])
testcase.update()

# List all general plan's children including their status
info("Listing child test plans of the general test plan")
for testplan in general_plan.children:
    print testplan, testplan.status

# Create a new test run
info("Creating a new test run")
testrun = nitrate.TestRun(
        testplan=release_plan,
        build="RHEL6.2-20110815.n.1",
        summary="python-2.6.6-20.el6.x86_64 / ER#11359")

# Get script and arguments for all IDLE performance caseruns, move to RUNNING
info("Scheduling performance tests")
for caserun in testrun:
    if (caserun.status == nitrate.Status("IDLE")
            and str(caserun.testcase.category) == "Performance"):
        print caserun.testcase.script, caserun.testcase.arguments
        caserun.status = nitrate.Status("RUNNING")
        caserun.update()

# Check case run status of the whole test run
info("Checking case run status")
for caserun in testrun:
    print caserun
