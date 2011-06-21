"""
High-level API for the Nitrate test case management system

This module provides a high-level python interface for the nitrate
module. Connection to the server is handled automatically by the
Nitrate object which checks user configuration file ~/.nitrate for
the "url" variable.

"""

import nitrate, sys, os
from nitrate import NitrateError
from pprint import pformat as pretty
from ConfigParser import SafeConfigParser, Error as ConfigParserError
import logging as log


def setLogLevel(level=None):
    """
    Set the default log level

    If the level is not specified environment variable DEBUG is
    used with the following meaning:

        DEBUG=0 ... Nitrate.log.WARN (default)
        DEBUG=1 ... Nitrate.log.INFO
        DEBUG=2 ... Nitrate.log.DEBUG
    """

    try:
        if level is None:
            level = {1: log.INFO, 2: log.DEBUG}[int(os.environ["DEBUG"])]
    except StandardError:
        level = log.WARN
    log.basicConfig(format="[%(levelname)s] %(message)s")
    log.getLogger().setLevel(level)

setLogLevel()


class Nitrate(object):
    """
    General Nitrate Object
    
    Takes care of initiating the connection to the Nitrate server,
    parses user configuration and handles the debugging mode.
    """
    _connection = None
    _settings = None
    _requests = 0

    @property
    def _config(self):
        """ User configuration (expected in ~/.nitrate). """

        # Read the config file (unless already done)
        if Nitrate._settings is None:
            try:
                path = os.path.expanduser("~/.nitrate")
                parser = SafeConfigParser()
                parser.read([path])
                Nitrate._settings = dict(parser.items("nitrate"))
            except ConfigParserError:
                raise NitrateError(
                        "Cannot read the config file {0}".format(path))

            # We need to know at least the server URL
            if "url" not in self._settings:
                raise NitrateError("No url found in the config file")

        # Return the settings
        return Nitrate._settings

    @property
    def _server(self):
        """ Connection to the Nitrate server. """

        # Connect to the server unless already connected
        if Nitrate._connection is None:
            log.info("Contacting server {0}".format(self._config["url"]))
            Nitrate._connection = nitrate.NitrateKerbXmlrpc(
                    self._config["url"]).server

        # Return existing connection
        Nitrate._requests += 1
        return Nitrate._connection

    def __str__(self):
        """ Provide a short summary about the connection. """

        return "Nitrate server: {0}\nTotal requests handled: {1}".format(
                self._config["url"], self._requests)


class Status(Nitrate):
    """
    Test case run status
    
    Used for easy converting between status id and name.
    """

    _statuses = ['PAD', 'IDLE', 'PASSED', 'FAILED', 'RUNNING', 'PAUSED',
            'BLOCKED', 'ERROR', 'WAIVED']

    def __init__(self, status):
        """
        Takes numeric status id (1-8) or status name which is one of:
        IDLE, PASSED, FAILED, RUNNING, PAUSED, BLOCKED, ERROR, WAIVED
        """
        if isinstance(status, int):
            self._id = status
        else:
            try:
                self._id = self._statuses.index(status)
            except ValueError:
                raise NitrateError("Invalid status '{0}'".format(status))

    def __str__(self):
        """ Return status name for printing. """
        return self.name

    def __eq__(self, other):
        """ Handle correctly status equality. """
        return self._id == other._id

    def __ne__(self, other):
        """ Handle correctly status inequality. """
        return self._id != other._id

    @property
    def id(self):
        """ Numeric status id. """
        return self._id

    @property
    def name(self):
        """ Human readable status name. """
        return self._statuses[self._id]


class NitrateMutable(Nitrate):
    """
    General class for all mutable Nitrate objects

    Implements default handling of object data access & updates.
    Provides the update() method which pushes the changes (if any)
    to the Nitrate server.
    """

    def __init__(self):
        # List of available attributes
        self._fields = []
        self._modified = False
        self.data = {}

    def __del__(self):
        """ Automatically update data upon destruction. """
        self.update()

    def __getattr__(self, name):
        """ Supported fields automatically dispatched for getting. """
        if name in self.__dict__.get("_fields", []):
            return self.data[name]
        else:
            return self.__dict__[name]

    def __setattr__(self, name, value):
        """ Allow direct field update, note modified state. """
        if name in self.__dict__.get("_fields", []):
            if self.data[name] != value:
                self.data[name] = value
                self._modified = True
                log.info("Updating {0} to {1}".format(name, value))
        else:
            object.__setattr__(self, name, value)

    def _update(self):
        """ Save data to server (to be implemented by respective class) """
        raise NitrateError("Data update not implemented")

    def update(self):
        """ Update the data, if modified, to the Nitrate server """
        if self._modified:
            self._update()
            self._modified = False


class TestPlan(NitrateMutable):
    """
    Provides 'testruns' and 'testcases' attributes, the latter as
    the default iterator. Supported fields: name
    """

    def __init__(self, id):
        """ Takes numeric plan id. """
        NitrateMutable.__init__(self)
        self._fields = "name".split()
        self.id = id
        self.data = self._server.TestPlan.get(id)
        log.info("TP#{0} fetched".format(self.id))
        log.debug(pretty(self.data))
        self._testruns = None
        self._testcases = None

    def __iter__(self):
        """ Provide test case list as the default iterator. """
        for testcase in self.testcases:
            yield testcase

    def __str__(self):
        """ Short test plan summary pro printing. """
        return "TP#{0} - {1} ({2} cases, {3} runs)".format(self.id,
                self.name, len(self.testcases), len(self.testruns))

    def _update(self):
        """ Save test plan data to the Nitrate server """
        hash = {"name": self.data["name"]}
        log.info("Updating TP#{0}".format(self.id))
        log.debug(pretty(hash))
        self._server.TestPlan.update(self.id, hash)


    @property
    def testruns(self):
        """ List of TestRun() objects related to this plan. """
        if self._testruns is None:
            self._testruns = [TestRun(hash) for hash in
                    self._server.TestPlan.get_test_runs(self.id)]

        return self._testruns

    @property
    def testcases(self):
        """ List of TestCase() objects related to this plan. """
        if self._testcases is None:
            self._testcases = [TestCase(hash) for hash in
                    self._server.TestPlan.get_test_cases(self.id)]

        return self._testcases


class TestRun(NitrateMutable):
    """
    Provides 'caseruns' attribute containing all relevant case
    runs. This is also the default iterator. Other supported
    fields: summary, notes
    """

    def __init__(self, data):
        """ Takes numeric id or test run hash. """
        NitrateMutable.__init__(self)
        self._fields = "summary notes".split()
        # Fetch the data hash from the server if id provided 
        if isinstance(data, int):
            self.id = data
            self.data = self._server.TestRun.get(self.id)
        # Otherwise just save the already-prepared data hash
        else:
            self.id = data["run_id"]
            self.data = data
        log.info("Fetched TR#{0}".format(self.id))
        log.debug(pretty(self.data))
        self._caseruns = None

    def __iter__(self):
        """ Provide test case run list as the default iterator. """
        for caserun in self.caseruns:
            yield caserun

    def __str__(self):
        """ Short test run summary pro printing. """
        return "TR#{0} - {1} ({2} cases)".format(
                self.id, self.summary, len(self.caseruns))

    def _update(self):
        """ Save test run data to the Nitrate server """
        # Filter out unsupported None values
        hash = {}
        hash["summary"] = self.data["summary"]
        hash["notes"] = self.data["notes"]
        log.info("Updating TR#{0}".format(self.id))
        log.debug(pretty(hash))
        self._server.TestRun.update(self.id, hash)

    @property
    def caseruns(self):
        """ List of TestCaseRun() objects related to this run. """
        if self._caseruns is None:
            # Fetch both test cases & test case runs
            testcases = self._server.TestRun.get_test_cases(self.id)
            caseruns = self._server.TestRun.get_test_case_runs(self.id)
            # Create the CaseRun objects
            self._caseruns = [TestCaseRun(testcase=testcase, caserun=caserun)
                    for caserun in caseruns for testcase in testcases
                    if testcase['case_id'] == caserun['case_id']]

        return self._caseruns


class TestCase(NitrateMutable):
    """
    Provides access to the test case fields. Following fields are
    supported: summary, notes, script and arguments.
    """

    def __init__(self, data):
        """ Takes numeric id or test case hash. """
        super(TestCase, self).__init__()
        self._fields = "summary notes script arguments".split()
        # Fetch the data hash from the server if numeric id provided 
        if isinstance(data, int):
            self.id = data
            self.data = self._server.TestCase.get(self.id)
        # Otherwise just save the already-prepared data hash
        else:
            self.id = data["case_id"]
            self.data = data
        log.info("Fetched TC#{0}".format(self.id))
        log.debug(pretty(self.data))

    def __str__(self):
        """ Short test case summary for printing. """
        return "TC#{0} - {1}".format(str(self.id).ljust(5), self.summary)

    def _update(self):
        """ Save test case data to Nitrate server """
        # Filter out unsupported None values
        hash = {}
        for (name, value) in self.data.iteritems():
            if value is not None:
                hash[name] = value
        log.info("Updating TC#{0}".format(self.id))
        log.debug(pretty(hash))
        self._server.TestCase.update(self.id, hash)


class TestCaseRun(NitrateMutable):
    """
    Provides access to the case run specific fields. Includes
    the 'testcase' attribute holding the respective test case
    object. Supported fields: status, notes
    """

    def __init__(self, id=None, testcase=None, caserun=None):
        """ Takes case run id or both test case and case run hashes. """
        NitrateMutable.__init__(self)
        self._fields = "notes".split()
        # Fetch the data hash from the server if id provided 
        if id is not None:
            self.data = self._server.TestCaseRun.get(id)
            self.testcase = TestCase(self.data["case_id"])
            self.id = id
        # Otherwise just save the already-prepared data hash
        else:
            self.testcase = TestCase(testcase)
            self.data = caserun
            self.id = caserun["case_run_id"]
        log.info("Fetched CR#{0}".format(self.id))
        log.debug(pretty(self.data))

    def __str__(self):
        """ Short test case summary pro printing. """
        return "{0} - CR#{1} - {2}".format(self.stat, str(self.id).ljust(6),
                self.testcase.data["summary"])

    def _update(self):
        """ Save test case run data to the Nitrate server """
        # Filter out unsupported None values
        hash = {}
        for (name, value) in self.data.iteritems():
            if value is not None:
                hash[name] = value
        # Different name for the status key in update()
        hash["case_run_status"] = hash["case_run_status_id"]
        log.info("Updating CR#{0}".format(self.id))
        log.debug(pretty(hash))
        self._server.TestCaseRun.update(self.id, hash)

    @property
    def status(self):
        """ Get case run status object """
        return Status(self.data["case_run_status_id"])

    @status.setter
    def status(self, newstatus):
        """ Set case run status """
        if self.status != newstatus:
            self.data["case_run_status_id"] = newstatus.id
            self._modified = True

    @property
    def stat(self):
        """ Short same-width status string (4 chars) """
        return self.status.name[0:4]


class Product(Nitrate): pass
class Build(Nitrate): pass
class Tag(Nitrate): pass
class Bug(Nitrate): pass


# Self-test
if __name__ == "__main__":
    # Display info about the server
    print Nitrate()

    # Show test plan summary and list test cases
    testplan = TestPlan(2214)
    print "\n", testplan
    for testcase in testplan:
        print ' ', testcase

    # For each test run list test cases with their status
    for testrun in testplan.testruns:
        print "\n", testrun
        for caserun in testrun:
            print ' ', caserun

    # Update test case data / case run status
    TestPlan(289).name = "Tessst plan"
    TestRun(6757).notes = "Testing notes"
    TestCase(46490).script = "/CoreOS/component/example"
    TestCaseRun(525318).status = Status("PASSED")

    # Display info about the server
    print Nitrate()
