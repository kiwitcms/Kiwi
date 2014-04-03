
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
Object id cannot be provided as string::

    − TestCase("1234")
    + TestCase(1234)

Tags are now regular objects and should be used instead of
strings (although for adding/removing and presence checking
backward compatiblity is preserved)::

    − "TestParametrized" in testcase.tags
    + Tag("TestParametrized") in testcase.tags

Default version has been moved from Product into TestPlan class.
Placing the default product version inside the Product class was
a mistake. The TestPlan class has been adjusted by adding a new
attribute 'version' as this is the proper place for this data::

    − Product(name="Fedora", version="20)
    + Product(name="Fedora")
    + Product("Fedora")

This is also why ``version`` is now a required field when creating
a new test plan::

    − TestPlan(name=A, product=B, type=C)
    + TestPlan(name=A, product=B, version=C, type=D)

Long ago obsoleted functions for setting log level, cache level
and coloring mode were removed, all log level constants are now
directly available in the main module::

    − setLogLevel(log.DEBUG)
    + set_log_level(LOG_DEBUG)

    − setColorMode(COLOR_OFF)
    + set_color_mode(COLOR_OFF)

    − setCacheLevel(CACHE_PERSISTENT)
    + set_cache_level(CACHE_PERSISTENT)
