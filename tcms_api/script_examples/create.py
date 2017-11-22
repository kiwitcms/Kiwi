#!/usr/bin/python
"""
Basic Example

Simple example showing the main features of the tcms_api module.
Covered are testplan, testrun, testcase creation, logging, setting the
log level, cache level and color mode, test case linking, attributes
adjustments and updating the changes to the server.
"""

import tcms_api
from tcms_api import info, log

# Set log level, cache level and color mode
tcms_api.set_log_level(tcms_api.LOG_DEBUG)
tcms_api.set_cache_level(tcms_api.CACHE_OBJECTS)
tcms_api.set_color_mode(tcms_api.COLOR_AUTO)

# Initialize an existing test plan
info("Initializing an existing test plan")
general_plan = tcms_api.TestPlan(3781)
print(general_plan)

# Logging, catching errors
tcms_api.set_log_level(tcms_api.LOG_INFO)
info("Initializing a bad test plan")
try:
    log.info("Inspecting the test plan")
    bad_plan = tcms_api.TestPlan(1)
    print(bad_plan)
except tcms_api.TCMSError as error:
    log.error("Bad test plan id ({0})".format(error))

# Iterate over all test plan's test cases
info("Inspecting test plan's test cases")
for testcase in general_plan:
    print(testcase)

# Create a new test plan
info("Creating a new test plan")
release_plan = tcms_api.TestPlan(
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
testcase = tcms_api.TestCase(
    summary="New performance test",
    product="Red Hat Enterprise Linux 6",
    category="Performance",
    script="/CoreOS/python/Performance/base")

# Set status, priority, default tester, add tags, attach bugs, link plans
info("Setting status, priority, tester, tags, bugs and plans")
testcase.status = tcms_api.CaseStatus("CONFIRMED")
testcase.priority = tcms_api.Priority("P1")
testcase.tester = tcms_api.User("psplicha")
testcase.tags.add(tcms_api.Tag("Tier1"))
testcase.bugs.add(tcms_api.Bug(bug=123))
testcase.testplans.add([general_plan, release_plan])
testcase.update()

# List all general plan's children including their status
info("Listing child test plans of the general test plan")
for testplan in general_plan.children:
    print(testplan, testplan.status)

# Create a new test run
info("Creating a new test run")
testrun = tcms_api.TestRun(
    testplan=release_plan,
    build="RHEL6.2-20110815.n.1",
    summary="python-2.6.6-20.el6.x86_64 / ER#11359")

# Get script and arguments for all IDLE performance caseruns, move to RUNNING
info("Scheduling performance tests")
for caserun in testrun:
    if (caserun.status == tcms_api.Status("IDLE") and
            str(caserun.testcase.category) == "Performance"):
        print(caserun.testcase.script, caserun.testcase.arguments)
        caserun.status = tcms_api.Status("RUNNING")
        caserun.update()

# Check case run status of the whole test run
info("Checking case run status")
for caserun in testrun:
    print(caserun)
