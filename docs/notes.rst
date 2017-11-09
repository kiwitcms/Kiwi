
======================
    Release Notes
======================

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    python-nitrate release notes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Manual section: 1
:Manual group: User Commands
:Date: February 2012

python-nitrate 1.0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
There have been many substantial changes in the python-nitrate
implementation and a bunch of new features have been added. Many
thanks to Filip Holec for contributing substantial part of the new
caching implementation. Here's the summary of important changes:

Improved Performance

- Common caching support for all Nitrate classes
- Persistent cache implementation, MultiCall support
- Cache().update() support for multicall slicing
- Experimental support for fetching data from Teiid

New Object Attributes

- TestPlan.owner attribute holding the default owner
- TestPlan.sortkey() for getting/setting test case order
- TestRun.testcases for easy iteration over linked cases
- TestRun.started and TestRun.finished timestamps
- TestCase.created for accessing the creation date

Other Features

- Huge api module refactored into several modules
- New utility functions header() and sliced() added
- Support for colored logging, new custom log levels
- Plain authentication supported in addition to Kerberos
- Improved man pages, module documentation and examples

Under the Hood

- The big cleanup of ininitialization and caching
- TestPlan.testruns reimplemented using PlanRuns container
- TestRun.caseruns and TestRun.testcases containers
- Test case containers iterate over sorted test cases
- Bugs reimplemented with containers and caching
- Store the initial object dict as _inject for future use

Test Suite

- New unit test cases implemented, many improved
- Added support for performance tests (--performance)
- Overall test summary printed at the end of testing

API Changes

Several backward-incompatible changes had to be introduced in
order to improve the performance and because of necessary cleanup.
Below you can find the list of differences in the module API.

Object id cannot be provided as string::

    − TestCase("1234")
    + TestCase(1234)

Tags are now regular objects and should be used instead of
strings (although for adding/removing and presence checking
backward compatiblity is silently preserved)::

    − testcase.tags.add("TestParametrized")
    + testcase.tags.add(Tag("TestParametrized"))
    − "TestParametrized" in testcase.tags
    + Tag("TestParametrized") in testcase.tags

Default version has been moved from Product into TestPlan class.
Placing the default product version inside the Product class was
by mistake. The TestPlan class has been adjusted by adding a new
attribute 'version' as this is the proper place for this data::

    − Product(name="Fedora", version="20)
    + Product(name="Fedora")
    + Product("Fedora")

This is also why ``version`` is now a required field when creating
a new test plan::

    − TestPlan(name=N, product=P, type=T)
    + TestPlan(name=N, product=P, version=V, type=T)

Long-ago obsoleted functions for setting log level, cache level
and coloring mode were removed, all log level constants are now
directly available in the main module::

    − setLogLevel(log.DEBUG)
    + set_log_level(LOG_DEBUG)

    − setColorMode(COLOR_OFF)
    + set_color_mode(COLOR_OFF)

    − setCacheLevel(CACHE_PERSISTENT)
    + set_cache_level(CACHE_PERSISTENT)

Utility function color() does not reflect the current color mode
automatically. Instead, new parameter 'enabled' should be used to
disable the coloring when desired, for example::

    color("txt", color="red", enabled=config.Coloring().enabled())
