#!/usr/bin/python

from nitrate import *

# Set log level, cache level and color mode
setLogLevel(log.DEBUG)
setCacheLevel(CACHE_OBJECTS)
setColorMode(COLOR_AUTO)

# Initialize an existing test plan
info("Initializing an existing test plan")
generalPlan = TestPlan(3781)
print generalPlan

# Logging, catching errors
setLogLevel(log.INFO)
info("Initializing a bad test plan")
try:
    log.info("Inspecting the test plan")
    badPlan = TestPlan(1)
    print badPlan
except NitrateError, e:
    log.error("Bad test plan id ({0})".format(e))

# Iterate over all test plan's test cases
info("Inspecting test plan's test cases")
for testcase in generalPlan:
    print testcase

# Create a new test plan
info("Creating a new test plan")
releasePlan = TestPlan(
        parent=generalPlan,
        name="python / rhel-6.2",
        type="Release",
        product="Red Hat Enterprise Linux 6",
        version="6.2")

# Link all automated test cases from the general plan
info("Linking automated test cases from the general plan")
for testcase in generalPlan:
    if testcase.automated:
        releasePlan.testcases.add(testcase)
releasePlan.update()

# Create a new test case
info("Creating a new test case")
testcase = TestCase(
        summary="New performance test",
        product="Red Hat Enterprise Linux 6",
        category="Performance",
        script="/CoreOS/python/Performance/new-test")

# Set status, priority, default tester, add tags, attach bugs, link plans
info("Setting status, priority, tester, tags, bugs and plans")
testcase.status = CaseStatus("CONFIRMED")
testcase.priority = Priority("P1")
testcase.tester = User("psplicha")
testcase.tags.add(Tag("Tier1"))
testcase.bugs.add(Bug(123))
testcase.testplans.add([generalPlan, releasePlan])
testcase.update()

# Beware of caching (reload objects if necessary)
info("Test plan synopsis (before update)")
print generalPlan.synopsis
print releasePlan.synopsis
generalPlan = TestPlan(generalPlan.id)
releasePlan = TestPlan(releasePlan.id)
info("Test plan synopsis (after update)")
print generalPlan.synopsis
print releasePlan.synopsis

# List all general plan's children including their status
info("Listing child test plans of the general test plan")
for testplan in TestPlan.search(parent=generalPlan.id):
    print testplan, testplan.status

# Create a new test run
info("Creating a new test run")
testrun = TestRun(
        testplan=releasePlan,
        build="RHEL6.2-20110815.n.1",
        summary="python-2.6.6-20.el6.x86_64 / ER#11359")

# Get script and arguments for all IDLE performance caseruns, move to RUNNING
info("Scheduling performance tests")
for caserun in testrun:
    if (caserun.status == Status("IDLE")
            and str(caserun.testcase.category) == "Performance"):
        print caserun.testcase.script, caserun.testcase.arguments
        caserun.status = Status("RUNNING")
        caserun.update()

# Check case run status of the whole test run
info("Checking case run status")
for caserun in testrun:
    print caserun
