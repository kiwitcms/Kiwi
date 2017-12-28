# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   Python API for the Kiwi TCMS test case management system.
#   Copyright (c) 2012 Red Hat, Inc. All rights reserved.
#   Author: Petr Splichal <psplicha@redhat.com>
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   This library is free software; you can redistribute it and/or
#   modify it under the terms of the GNU Lesser General Public
#   License as published by the Free Software Foundation; either
#   version 2.1 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
Container classes implementation

All container classes are mutable objects which contain other TCMS
objects and have methods for adding and removing objects to/from the
container, for example adding a tag to a test case:

    testcase = TestCase(12345)
    testcase.tags.add(Tag("Tier1"))
    testcase.tags.remove(Tag("Tier2"))
    testcase.update()

Use add() for adding an object to the container, remove() for removing
an object and clear() for removing all items from it.

Container overview (objects contained are listed in brackets):

    TestPlan.tags = PlanTags[Tag] ......................... done
    TestPlan.components = PlanComponents[Component] ....... done
    TestPlan.children = ChildPlans[TestPlan] .............. done
    TestPlan.testcases = PlanCases[TestCase] .............. done
    TestPlan.testruns = PlanRuns[TestRun] ................. done
    TestPlan.caseplans = PlanCasePlans[CasePlan] .......... done

    TestRun.tags = RunTags[Tag] ........................... done
    TestRun.caseruns = RunCaseRuns[CaseRun] ............... done
    TestRun.testcases = RunCases[TestCase] ................ done

    TestCase.tags = CaseTags[Tag] ......................... done
    TestCase.components = CaseComponents[Component] ....... done
    TestCase.testplans = CasePlans[TestPlan] .............. done
    TestCase.testruns = CaseRuns[TestRun] ................. needed?
    TestCase.caseruns = CaseCaseRuns[CaseRun] ............. needed?
    TestCase.caseplans = CaseCasePlans[CasePlan] .......... needed?
    TestCase.bugs = CaseBugs[Bug] ......................... done

    CaseRun.bugs = CaseRunBugs[Bug] ....................... done
"""

import xmlrpc.client
from pprint import pformat as pretty

import tcms_api.config as config

from tcms_api.config import log
from tcms_api.utils import listed
from tcms_api.base import TCMS, TCMSNone, _getter, _idify
from tcms_api.immutable import Component, Bug, Tag
from tcms_api.xmlrpc import TCMSError
from tcms_api.mutable import (
    Mutable, TestPlan, TestRun, TestCase, CaseRun, CasePlan)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Container Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Container(Mutable):
    """
    General container class for handling sets of objects.

    Provides the add() and remove() methods for adding and removing
    objects and the internal _add() and _remove() which perform the
    actual update to the server (implemented by respective class).
    """

    # List of all object attributes (used for init & expiration)
    _attributes = ["current", "original"]

    # Class of objects to be contained (defined in each container)
    _class = None

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Container Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    id = property(_getter("id"), doc="Related object id.")

    @property
    def _items(self):
        """ Set representation containing the items """
        if self._current is TCMSNone:
            self._fetch()
        # Fetch the whole container if there are uncached items (except when
        # the container is modified otherwise we would lose local changes).
        if not self._modified and not self._class._is_cached(self._current):
            self._fetch()
        return self._current

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Container Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __new__(cls, object, inset=None):
        """ Create new container objects based on the object id """
        return super(Container, cls).__new__(cls, object.id)

    def __init__(self, object, inset=None):
        """ Initialize container for specified object """
        # Initialize (unless already done)
        if self._id is not None:
            # Initialized but not fetched ---> fetch from the inset if given
            if inset is not None and not self._is_cached(self):
                self._fetch(inset)
            return
        Mutable.__init__(self, object.id)
        self._identifier = object.identifier
        self._object = object
        # Initialize directly if initial set provided
        if inset is not None:
            self._fetch(inset)

    def __iter__(self):
        """ Container iterator """
        for item in self._items:
            yield item

    def __getitem__(self, index):
        """ Indexing support """
        if isinstance(index, int):
            return list(self)[index]
        elif isinstance(index, slice):
            return list(self)[index.start:index.stop:index.step]
        else:
            raise IndexError("Invalid index '{0}'".format(index))

    def __contains__(self, item):
        """ Container 'in' operator """
        return item in self._items

    def __len__(self):
        """ Number of container items """
        return len(self._items)

    def __str__(self):
        """ Display items as a list for printing """
        if self._items:
            # List of identifiers
            try:
                return listed(sorted(
                    [item.identifier for item in self._items]))
            # If no identifiers, just join strings
            except AttributeError:
                return listed(self._items, quote="'")
        else:
            return "[None]"

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Container Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inset=None):
        """ Save cache timestamp and initialize from inset if given """
        TCMS._fetch(self)
        # Create copies of the initial set (if given)
        if inset is not None:
            log.debug("Initializing {0} for {1} from the inset".format(
                self.__class__.__name__, self._identifier))
            log.debug(pretty(inset))
            self._current = set(inset)
            self._original = set(inset)
        # cache into container class
        if config.get_cache_level() >= config.CACHE_OBJECTS:
            self.__class__._cache[self._id] = self
        # Return True if the data are already initialized
        return inset is not None

    def add(self, items):
        """ Add an item or a list of items to the container """

        # Convert to set representation
        if isinstance(items, list):
            items = set(items)
        else:
            items = set([items])

        # If there are any new items
        add_items = items - self._items
        if add_items:
            log.info("Adding {0} to {1}'s {2}".format(
                listed([item.identifier for item in add_items],
                       self._class.__name__, max=10),
                self._object.identifier,
                self.__class__.__name__))
            self._items.update(items)
            if config.get_cache_level() != config.CACHE_NONE:
                self._modified = True
            else:
                self._update()

    def remove(self, items):
        """ Remove an item or a list of items from the container """

        # Convert to set representation
        if isinstance(items, list):
            items = set(items)
        else:
            items = set([items])

        # If there are any items to be removed
        remove_items = items.intersection(self._items)
        if remove_items:
            log.info("Removing {0} from {1}'s {2}".format(
                listed([item.identifier for item in remove_items],
                       self._class.__name__, max=10),
                self._object.identifier,
                self.__class__.__name__))
            self._items.difference_update(items)
            if config.get_cache_level() != config.CACHE_NONE:
                self._modified = True
            else:
                self._update()

    def clear(self):
        """ Remove all items from the container """
        self.remove(list(self._items))

    def _add(self, items):
        """ Add provided items to the server """
        raise TCMSError("To be implemented by respective class.")

    def _remove(self, items):
        """ Remove provided items from the server """
        raise TCMSError("To be implemented by respective class.")

    def _update(self):
        """ Update container changes to the server """
        # Added items
        added = self._current - self._original
        if added:
            self._add(added)

        # Removed items
        removed = self._original - self._current
        if removed:
            self._remove(removed)

        # Save the current state as the original (for future updates)
        self._original = set(self._current)

    def _sleep(self):
        """ Prepare container items for caching """
        # When restoring the container from the cache, unpickling failed
        # because of trying to construct set() of objects which were not
        # fully rebuild yet (__hash__ failed because of missing self._id).
        # So we need to convert containers into list of ids before the
        # cache dump and instantiate the objects back after cache restore.
        if self._current is TCMSNone:
            return

        self._original = [item.id for item in self._original]
        self._current = [item.id for item in self._current]

    def _wake(self):
        """ Restore container object after loading from cache """
        # See _sleep() method above for explanation why this is necessary
        if self._current is TCMSNone:
            return

        if self._class._is_cached(list(self._original)):
            log.cache("Waking up {0} for {1}".format(
                self.__class__.__name__, self._identifier))
            self._original = set([self._class(id) for id in self._original])
            self._current = set([self._class(id) for id in self._current])
        else:
            log.cache("Skipping wake up of {0} for {1}".format(
                self.__class__.__name__, self._identifier))
            self._init()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#   Case Components Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class CaseComponents(Container):
    """ Components linked to a test case """

    # Local cache indexed by corresponding test case id
    _cache = {}
    # Class of contained objects
    _class = Component

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Case Components Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __str__(self):
        """ The list of linked components' names """
        if self._items:
            return listed(sorted([component.name for component in self]))
        else:
            return "[None]"

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Case Components Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inset=None):
        """ Fetch currently linked components from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching {0}'s components".format(self._identifier))
        self._current = set([Component(inject)
                            for inject in self._server.TestCase.get_components(self.id)])
        self._original = set(self._current)

    def _add(self, components):
        """ Link provided components to the test case """
        log.info("Linking {1} to {0}".format(
            self._identifier,
            listed([component.name for component in components])))
        data = [component.id for component in components]
        log.data(data)
        self._server.TestCase.add_component(self.id, data)

    def _remove(self, components):
        """ Unlink provided components from the test case """
        for component in components:
            log.info("Unlinking {0} from {1}".format(
                component.name, self._identifier))
            self._server.TestCase.remove_component(self.id, component.id)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#   Plan Components Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class PlanComponents(Container):
    """ Components linked to a test plan """

    # Local cache indexed by corresponding test plan id
    _cache = {}
    # Class of contained objects
    _class = Component

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Plan Components Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __str__(self):
        """ The list of linked components' names """
        if self._items:
            return listed(sorted([component.name for component in self]))
        else:
            return "[None]"

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Plan Components Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inset=None):
        """ Fetch currently linked components from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching {0}'s components".format(self._identifier))
        self._current = set([Component(inject)
                            for inject in self._server.TestPlan.get_components(self.id)])
        self._original = set(self._current)

    def _add(self, components):
        """ Link provided components to the test plan """
        log.info("Linking {1} to {0}".format(
            self._identifier,
            listed([component.name for component in components])))
        data = [component.id for component in components]
        log.data(data)
        self._server.TestPlan.add_component(self.id, data)

    def _remove(self, components):
        """ Unlink provided components from the test plan """
        for component in components:
            log.info("Unlinking {0} from {1}".format(
                component.name, self._identifier))
            self._server.TestPlan.remove_component(self.id, component.id)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Case Bugs Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class CaseBugs(Container):
    """ Bugs attached to a test case """

    # Local cache of bugs attached to a test case
    _cache = {}

    # Class of contained objects
    _class = Bug

    def _fetch(self, inset=None):
        """ Fetch currently attached bugs from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching bugs for {0}".format(self._identifier))
        injects = self._server.TestCase.get_bugs(self.id)
        log.data(pretty(injects))
        self._current = set([Bug(inject) for inject in injects])
        self._original = set(self._current)

    def _add(self, bugs):
        """ Attach provided bugs to the test case """
        log.info("Attaching {0} to {1}".format(
            listed(bugs), self._identifier))
        data = [{
                "bug_id": bug.bug,
                "bug_system_id": bug.system,
                "case_id": self.id} for bug in bugs]
        log.data(pretty(data))
        self._server.TestCase.attach_bug(data)
        # Fetch again the whole bug list (to get the internal id)
        self._fetch()

    def _remove(self, bugs):
        """ Detach provided bugs from the test case """
        log.info("Detaching {0} from {1}".format(
            listed(bugs), self._identifier))
        data = [bug.bug for bug in bugs]
        log.data(pretty(data))
        self._server.TestCase.detach_bug(self.id, data)

    # Print unicode list of bugs
    def __str__(self):
        return listed(self._items)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Case Run Bugs Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class CaseRunBugs(Container):
    """ Bugs attached to a test case run """

    # Local cache of bugs attached to a test case
    _cache = {}

    # Class of contained objects
    _class = Bug

    def _fetch(self, inset=None):
        """ Fetch currently attached bugs from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching bugs for {0}".format(self._identifier))
        injects = self._server.TestCaseRun.get_bugs({'case_run': self.id})
        log.data(pretty(injects))
        self._current = set([Bug(inject) for inject in injects])
        self._original = set(self._current)

    def _add(self, bugs):
        """ Attach provided bugs to the test case """
        log.info("Attaching {0} to {1}".format(
            listed(bugs), self._identifier))
        data = [{
                "bug_id": bug.bug,
                "bug_system_id": bug.system,
                "case_run_id": self.id} for bug in bugs]
        log.data(pretty(data))
        self._server.TestCaseRun.attach_bug(data)
        # Fetch again the whole bug list (to get the internal id)
        self._fetch()

    def _remove(self, bugs):
        """ Detach provided bugs from the test case """
        log.info("Detaching {0} from {1}".format(
            listed(bugs), self._identifier))
        data = [bug.bug for bug in bugs]
        log.data(pretty(data))
        self._server.TestCaseRun.detach_bug(self.id, data)

    # Print unicode list of bugs
    def __str__(self):
        return listed(self._items)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  TagContainer Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class TagContainer(Container):
    """ Tag container with support for string tags """

    def __contains__(self, tag):
        """ Tag 'in' operator """
        tag = Tag(tag) if isinstance(tag, str) else tag
        return tag in self._items

    def add(self, tags):
        """ Add a tag or a list of tags """
        tags = [tags] if not isinstance(tags, list) else tags
        tags = [Tag(tag) if isinstance(tag, str) else tag
                for tag in tags]
        super(TagContainer, self).add(tags)

    def remove(self, tags):
        """ Remove a tag or a list of tags """
        tags = [tags] if not isinstance(tags, list) else tags
        tags = [Tag(tag) if isinstance(tag, str) else tag
                for tag in tags]
        super(TagContainer, self).remove(tags)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Plan Tags Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class PlanTags(TagContainer):
    """ Test plan tags """

    _cache = {}

    # Class of contained objects
    _class = Tag

    def _fetch(self, inset=None):
        """ Fetch currently attached tags from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching tags for {0}".format(self._identifier))
        injects = self._server.TestPlan.get_tags(self.id)
        log.debug(pretty(injects))
        self._current = set([Tag(inject) for inject in injects])
        self._original = set(self._current)

    def _add(self, tags):
        """ Attach provided tags to the test plan """
        log.info("Tagging {0} with {1}".format(
            self._identifier, listed(tags, quote="'")))
        self._server.TestPlan.add_tag(self.id, list(tag.name for tag in tags))

    def _remove(self, tags):
        """ Detach provided tags from the test plan """
        log.info("Untagging {0} of {1}".format(
            self._identifier, listed(tags, quote="'")))
        self._server.TestPlan.remove_tag(self.id, list(
            tag.name for tag in tags))

    # Print unicode list of tags
    def __str__(self):
        return listed(self._items, quote="'")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Run Tags Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class RunTags(TagContainer):
    """ Test run tags """

    _cache = {}

    # Class of contained objects
    _class = Tag

    def _fetch(self, inset=None):
        """ Fetch currently attached tags from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching tags for {0}".format(self._identifier))
        injects = self._server.TestRun.get_tags(self.id)
        log.debug(pretty(injects))
        self._current = set([Tag(inject) for inject in injects])
        self._original = set(self._current)

    def _add(self, tags):
        """ Attach provided tags to the test run """
        log.info("Tagging {0} with {1}".format(
            self._identifier, listed(tags, quote="'")))
        self._server.TestRun.add_tag(self.id, list(tag.name for tag in tags))

    def _remove(self, tags):
        """ Detach provided tags from the test run """
        log.info("Untagging {0} of {1}".format(
            self._identifier, listed(tags, quote="'")))
        self._server.TestRun.remove_tag(self.id, list(
            tag.name for tag in tags))

    # Print unicode list of tags
    def __str__(self):
        return listed(self._items, quote="'")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Case Tags Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class CaseTags(TagContainer):
    """ Test case tags """

    _cache = {}

    # Class of contained objects
    _class = Tag

    def _fetch(self, inset=None):
        """ Fetch currently attached tags from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching tags for {0}".format(self._identifier))
        injects = self._server.TestCase.get_tags(self.id)
        log.debug(pretty(injects))
        self._current = set([Tag(inject) for inject in injects])
        self._original = set(self._current)

    def _add(self, tags):
        """ Attach provided tags to the test case """
        log.info("Tagging {0} with {1}".format(
            self._identifier, listed(tags, quote="'")))
        self._server.TestCase.add_tag(self.id, list(tag.name for tag in tags))

    def _remove(self, tags):
        """ Detach provided tags from the test case """
        log.info("Untagging {0} of {1}".format(
            self._identifier, listed(tags, quote="'")))
        self._server.TestCase.remove_tag(self.id, list(tag.name for tag in tags))

    # Print unicode list of tags
    def __str__(self):
        return listed(self._items, quote="'")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Case Plans Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class CasePlans(Container):
    """ Test plans linked to a test case """

    _cache = {}

    # Class of contained objects
    _class = TestPlan

    def _fetch(self, inset=None):
        """ Fetch currently attached tags from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching {0}'s plans".format(self._identifier))
        self._current = set([TestPlan(inject)
                            for inject in self._server.TestCase.get_plans(self.id)])
        self._original = set(self._current)

    def _add(self, plans):
        """ Link provided plans to the test case """
        log.info("Linking {1} to {0}".format(
            self._identifier,
            listed([plan.identifier for plan in plans])))
        self._server.TestCase.link_plan(self.id, [plan.id for plan in plans])

    def _remove(self, plans):
        """ Unlink provided plans from the test case """
        for plan in plans:
            log.info("Unlinking {0} from {1}".format(
                plan.identifier, self._identifier))
            self._server.TestCase.unlink_plan(self.id, plan.id)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Plan Runs Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class PlanRuns(Container):
    """ Test runs related to a test plan """

    # Local cache of test runs for a test plan
    _cache = {}

    # Class of contained objects
    _class = TestRun

    def _fetch(self, inset=None):
        """ Fetch test runs from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching testruns for {0}".format(self._identifier))
        injects = self._server.TestPlan.get_test_runs(self.id)
        log.data(pretty(injects))
        self._current = set([TestRun(inject) for inject in injects])
        self._original = set(self._current)

    def _add(self, testruns):
        """ New test runs are created using TestRun() constructor """
        raise TCMSError(
            "Use TestRun(testplan=X) for creating a new test run")

    def _remove(self, testruns):
        """ Currently no support for removing test runs from test plans """
        raise TCMSError("Sorry, no support for removing test runs yet")

    def __iter__(self):
        """ Iterate over test runs ordered by their id/creation """
        for testrun in sorted(self._items, key=lambda x: x.id):
            yield testrun

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Test Cases Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class PlanCases(Container):
    """ Test cases linked to a test plan """

    _cache = {}

    # Class of contained objects
    _class = TestCase

    def _fetch(self, inset=None):
        """ Fetch currently linked test cases from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        # Initialize all plan-case tags (skip when caching persistently
        # as this an additional/unnecessary call in that case)
        if config.get_cache_level() == config.CACHE_OBJECTS:
            log.info("Fetching tags for all {0}'s test cases".format(
                self._object.identifier))
            for tag in self._server.TestPlan.get_all_cases_tags(self.id):
                Tag(tag)
        # Fetch test cases from the server
        log.info("Fetching {0}'s cases".format(self._identifier))
        injects = self._server.TestPlan.get_test_cases(self.id)
        log.data("Fetched {0}".format(listed(injects, "inject")))
        self._current = set([TestCase(inject) for inject in injects])
        self._original = set(self._current)
        # Initialize case plans if not already cached
        if not PlanCasePlans._is_cached(self._object.caseplans):
            inset = [CasePlan({
                # Fake our own internal id from testplan & testcase
                "id": _idify([self._object.id, inject["case_id"]]),
                "case_id": inject["case_id"],
                "plan_id": self._object.id,
                "sortkey": inject["sortkey"]
            }) for inject in injects]
            self._object.caseplans._fetch(inset)

    def _add(self, cases):
        """ Link provided cases to the test plan """
        # Link provided cases on the server
        log.info("Linking {1} to {0}".format(
            self._identifier,
            listed([case.identifier for case in cases])))
        self._server.TestCase.link_plan([case.id for case in cases], self.id)
        # Add corresponding CasePlan objects to the PlanCasePlans container
        if PlanCasePlans._is_cached(self._object.caseplans):
            self._object.caseplans.add([
                CasePlan(testcase=case, testplan=self._object)
                for case in cases])

    def _remove(self, cases):
        """ Unlink provided cases from the test plan """
        # Unlink provided cases on the server
        for case in cases:
            log.info("Unlinking {0} from {1}".format(
                case.identifier, self._identifier))
            self._server.TestCase.unlink_plan(case.id, self.id)
        # Add corresponding CasePlan objects from the PlanCasePlans container
        if PlanCasePlans._is_cached(self._object.caseplans):
            self._object.caseplans.remove([
                CasePlan(testcase=case, testplan=self._object)
                for case in cases])

    def __iter__(self):
        """ Iterate over all included test cases ordered by sortkey """
        for testcase in sorted(
                self._items, key=lambda x: self._object.sortkey(x)):
            yield testcase

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Child Plans
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class ChildPlans(Container):
    """ Child test plans of a parent plan """

    _cache = {}

    # Class of contained objects
    _class = TestPlan

    def _fetch(self, inset=None):
        """ Find all child test plans """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching {0}'s child plans".format(self._identifier))
        self._current = set(TestPlan.search(parent=self.id))
        self._original = set(self._current)

    def _add(self, plans):
        """ Set self as parent of given test plans """
        log.info("Setting {1} as parent of {0}".format(
            self._identifier,
            listed([plan.identifier for plan in plans])))
        for plan in plans:
            plan.parent = TestPlan(self.id)
            plan.update()

    def _remove(self, plans):
        """ Remove self as parent of given test plans """
        log.info("Removing {1} as parent of {0}".format(
            self._identifier,
            listed([plan.identifier for plan in plans])))
        for plan in plans:
            plan.parent = None
            plan.update()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  RunCases Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class RunCases(Container):
    """ Test case objects related to a test run """

    # Local cache of test cases for a test run
    _cache = {}

    # Class of contained objects
    _class = TestCase

    def _fetch(self, inset=None):
        """ Fetch test run cases from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        # Fetch attached test cases from the server
        log.info("Fetching {0}'s test cases".format(self._identifier))
        injects = self._server.TestRun.get_test_cases(self.id)
        self._current = set([TestCase(inject) for inject in injects])
        self._original = set(self._current)

    def _add(self, testcases):
        """ Add given test cases to the test run """
        # Short info about the action
        identifiers = [testcase.identifier for testcase in testcases]
        log.info("Adding {0} to {1}".format(
            listed(identifiers, "testcase", max=3),
            self._object.identifier))
        # Prepare data and push
        data = [testcase.id for testcase in testcases]
        log.data(pretty(data))
        try:
            self._server.TestRun.add_cases(self.id, data)
        # Handle duplicate entry errors by adding test cases one by one
        except xmlrpc.client.Fault as error:
            if "Duplicate entry" not in str(error):
                raise
            log.warn(error)
            for id in data:
                try:
                    self._server.TestRun.add_cases(self.id, id)
                except xmlrpc.client.Fault:
                    pass

        # RunCaseRuns will need update ---> erase current data
        self._object.caseruns._init()

    def _remove(self, testcases):
        """ Remove given test cases from the test run """
        # Short info about the action
        identifiers = [testcase.identifier for testcase in testcases]
        log.info("Removing {0} from {1}".format(
            listed(identifiers, "testcase", max=3),
            self._object.identifier))
        data = [testcase.id for testcase in testcases]
        log.data(pretty(data))
        self._server.TestRun.remove_cases(self.id, data)
        # RunCaseRuns will need update ---> erase current data
        self._object.caseruns._init()

    def __iter__(self):
        """ Iterate over all included test cases ordered by sortkey """
        for caserun in sorted(self._object.caseruns, key=lambda x: x.sortkey):
            yield caserun.testcase

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  RunCaseRuns Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class RunCaseRuns(Container):
    """ Test case run objects related to a test run """

    # Local cache of test case runs for a test run
    _cache = {}

    # Class of contained objects
    _class = CaseRun

    def _fetch(self, inset=None):
        """ Fetch case runs from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        # Fetch test case runs from the server
        log.info("Fetching {0}'s case runs".format(self._identifier))
        injects = self._server.TestRun.get_test_case_runs(self.id)
        # Feed the TestRun.testcases container with the initial object
        # set if all cases are already cached (saving unnecesary fetch)
        testcaseids = [inject["case_id"] for inject in injects]
        if (not RunCases._is_cached(self._object.testcases) and
                TestCase._is_cached(testcaseids)):
            self._object.testcases._fetch([TestCase(id) for id in testcaseids])
        # And finally create the initial object set
        self._current = set([CaseRun(inject, testcaseinject=testcase)
                            for inject in injects
                            for testcase in self._object.testcases._items
                            if int(inject["case_id"]) == testcase.id])
        self._original = set(self._current)

    def _add(self, caseruns):
        """ Adding supported by CaseRun() or TestRun.testcases.add() """
        raise TCMSError(
            "Use TestRun.testcases.add([testcases]) to add new test cases")

    def _remove(self, caseruns):
        """ Removing supported by TestRun.testcases.remove() """
        raise TCMSError(
            "Use TestRun.testcases.remove([testcases]) to remove cases")

    def __iter__(self):
        """ Iterate over all included case runs ordered by sortkey """
        for caserun in sorted(self._items, key=lambda x: x.sortkey):
            yield caserun

    def update(self):
        """ Update modified case runs"""
        # Check for modified case runs
        modified = [caserun for caserun in self if caserun._modified]
        if not modified:
            return
        log.info("Updating {0}'s case runs".format(self._identifier))
        # Update modified caseruns
        for caserun in modified:
            caserun._update()
            caserun._modified = False

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  PlanCasePlans Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class PlanCasePlans(Container):
    """ Test case plan objects related to a test plan """

    # Local cache & class of contained objects
    _cache = {}
    _class = CasePlan

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  PlanCasePlans Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inset=None):
        """ Fetch case plans from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return

        # Fetch test case plans from the server
        log.info("Fetching case plans for {0}".format(self._identifier))
        injects = []
        for testcase in self._object.testcases._items:
            injects.append(self._server.TestCasePlan.get(testcase.id, self._object.id))
        log.data(pretty(injects))

        # And finally create the initial object set
        self._current = set([CasePlan(inject) for inject in injects])
        self._original = set(self._current)

    def _add(self, caseplans):
        """ Test case linking is handled by PlanCases class """
        # Nothing to do on our side
        pass

    def _remove(self, caseplans):
        """ Test case unlinking is handled by PlanCases class """
        # Nothing to do on our side
        pass

    def add(self, caseplans):
        """ Add case plans to the container """
        # The method is used just for sync with PlanCases, we never add
        # CasePlans to the server, thus we never get modified
        super(PlanCasePlans, self).add(caseplans)
        self._modified = False

    def remove(self, caseplans):
        """ Remove case plans from the container """
        # The method is used just for sync with PlanCases, we never remove
        # CasePlans to the server, thus we never get modified
        super(PlanCasePlans, self).remove(caseplans)
        self._modified = False

    def update(self):
        """ Update case plans with modified sortkey """
        modified = [caseplan for caseplan in self if caseplan._modified]
        # Nothing to do if there are no sortkey changes
        if not modified:
            return
        # Update all modified caseplans
        log.info("Updating {0}'s case plans".format(self._identifier))
        for caseplan in modified:
            caseplan._update()
            caseplan._modified = False
