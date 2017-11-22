#!/usr/bin/python

import re, sys, optparse
from tcms_api import *

if __name__ == "__main__":
    parser = optparse.OptionParser(usage="matrix.py --plan PLAN [options]")
    parser.add_option("--plan", dest="plan", type="int", help="test plan id")
    options = parser.parse_args()[0]

    testplan = TestPlan(options.plan)
    print "Checking results of {0}:\nTest runs: {1}".format(testplan,
            ", ".join([run.identifier for run in testplan.testruns]))

    for testcase in sorted(testplan.testcases, key=lambda x: x.script):
        for testrun in testplan.testruns:
            for caserun in testrun.caseruns:
                if caserun.testcase.id == testcase.id:
                    print caserun.status.shortname,
                    break
            else:
                print "....",
        print "- {0} - {1}".format(str(testcase.tester).ljust(8), testcase)
